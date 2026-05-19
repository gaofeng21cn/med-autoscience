from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_text


def test_portal_console_soak_checks_user_parity_evidence_keys(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.portal_console_soak")
    profile = make_profile(tmp_path)
    root = profile.workspace_root
    portal_payload_path = root / "artifacts" / "runtime" / "progress_portal" / "latest.json"
    portal_html_path = root / "ops" / "mas" / "progress" / "index.html"
    console_payload_path = root / "artifacts" / "runtime" / "live_console" / "session_read_model" / "latest.json"
    console_ui_payload_path = root / "artifacts" / "runtime" / "live_console" / "ui_payload" / "latest.json"
    console_html_path = root / "ops" / "mas" / "live-console" / "index.html"
    conversation_payload_path = root / "artifacts" / "runtime" / "conversation_read_model" / "latest.json"
    study_page_html = root / "ops" / "mas" / "progress" / "studies" / "DM002" / "index.html"
    study_page_payload = root / "artifacts" / "runtime" / "progress_portal" / "studies" / "DM002" / "latest.json"

    route_trail = {
        "surface_kind": "mas_progress_portal_route_decision_trail",
        "status": "available",
        "active_path": "analysis-route-b",
        "winning_path": "analysis-route-b",
        "nodes": [
            {
                "route_id": "analysis-route-b",
                "label": "Analysis route B",
                "decision": "continue",
                "evidence_point": "primary model converged",
                "pivot_rationale": "route A lacked source refs",
            }
        ],
        "source_refs": ["studies/DM002/artifacts/runtime/route_trail/latest.json"],
    }
    route_map = {
        "surface_kind": "mas_progress_portal_route_map",
        "status": "available",
        "active_path": "analysis-route-b",
        "winning_path": "analysis-route-b",
        "nodes": [
            {
                "id": "stage-current",
                "kind": "stage",
                "label": "当前阶段：analysis",
                "status": "current",
                "summary": "analysis route has started",
                "source_refs": ["studies/DM002/artifacts/runtime/route_trail/latest.json"],
                "artifact_refs": [],
                "conversation_refs": [],
            },
            {
                "id": "route-analysis-route-b",
                "kind": "route",
                "label": "Analysis route B",
                "status": "active",
                "summary": "primary model converged",
                "source_refs": ["studies/DM002/artifacts/runtime/route_trail/latest.json"],
                "artifact_refs": [],
                "conversation_refs": [],
            },
            {
                "id": "decision-analysis-route-b",
                "kind": "decision",
                "label": "路线决策",
                "status": "active",
                "summary": "切换理由：route A lacked source refs",
                "source_refs": ["studies/DM002/artifacts/runtime/route_trail/latest.json"],
                "artifact_refs": [],
                "conversation_refs": ["conversation-seq-2"],
            },
        ],
        "edges": [
            {
                "from": "stage-current",
                "to": "route-analysis-route-b",
                "kind": "advance",
                "label": "推进",
                "status": "available",
                "source_refs": ["studies/DM002/artifacts/runtime/route_trail/latest.json"],
            },
            {
                "from": "route-analysis-route-b",
                "to": "decision-analysis-route-b",
                "kind": "advance",
                "label": "决策",
                "status": "available",
                "source_refs": ["studies/DM002/artifacts/runtime/route_trail/latest.json"],
            },
        ],
        "source_refs": ["studies/DM002/artifacts/runtime/route_trail/latest.json"],
    }
    study_workbench = {
        "surface_kind": "mas_progress_portal_study_workbench",
        "tabs": [
            {"id": "overview"},
            {"id": "route_map"},
            {"id": "route_decision_trail"},
            {"id": "path_stage"},
            {"id": "runtime"},
            {"id": "artifacts"},
            {"id": "conversation"},
            {"id": "source_refs"},
        ],
        "route_map": route_map,
        "route_decision_trail": route_trail,
        "conversation": {
            "surface_kind": "mas_progress_portal_conversation_panel",
            "status": "available",
            "study_id": "DM002",
            "timeline_items": [
                {
                    "sequence": 1,
                    "item_kind": "user_message",
                    "message_id": "msg-dm002",
                    "message_status": "completed",
                    "source_ref": "studies/DM002/artifacts/runtime/user_message_queue.json",
                },
                {
                    "sequence": 2,
                    "item_kind": "turn_receipt",
                    "run_id": "run-dm002",
                    "turn_status": "completed",
                    "tool_refs": ["tool=study_progress"],
                    "source_ref": "studies/DM002/artifacts/runtime/turn_receipts/turn-001.json",
                },
            ],
            "source_refs": [
                "artifacts/runtime/conversation_read_model/latest.json",
                "studies/DM002/artifacts/runtime/turn_receipts/turn-001.json",
            ],
        },
    }
    portal_payload = {
        "generated_at": "2026-05-09T01:00:00+00:00",
        "freshness": {"status": "fresh", "latest_event_at": "2026-05-09T00:59:00+00:00"},
        "workspace": {
            "studies": [
                {
                    "study_id": "DM002",
                    "portal_href": "studies/DM002/index.html",
                    "live_console_href": "../live-console/index.html?study_id=DM002",
                },
                {
                    "study_id": "DPCC003",
                    "portal_href": "studies/DPCC003/index.html",
                    "live_console_href": "../live-console/index.html?study_id=DPCC003",
                },
            ],
        },
        "study": {
            "outer_supervision_slo": {"surface_kind": "outer_supervision_slo", "state": "fresh"},
        },
        "study_workbench": study_workbench,
        "live_console": {"html_ref": "ops/mas/live-console/index.html?study_id=DM002"},
        "opl_handoff": {"deep_link": "ops/mas/progress/studies/DM002/index.html"},
        "source_refs": ["studies/DM002/artifacts/runtime/health/latest.json"],
    }
    console_snapshot = {
        "selected_study_id": "DM002",
        "studies": [
            {"study_id": "DM002", "selected": True, "runs": [{"run_id": "run-dm002"}]},
            {"study_id": "DPCC003", "selected": False, "runs": []},
        ],
        "stream_sources": [
            {
                "topic": "terminal.tail",
                "study_id": "DM002",
                "source_ref": "runtime/quests/dm002/stdout.jsonl",
                "status": "available",
            },
            {
                "topic": "log.tail",
                "study_id": "DM002",
                "source_ref": "runtime/quests/dm002/stderr.txt",
                "status": "available",
            },
        ],
        "controller_action_intents": [
            {
                "intent": "request_reconcile",
                "executes_directly": False,
                "command": "medautosci runtime domain-route-reconcile --profile <profile> --study-id DM002",
            }
        ],
        "events": [{"topic": "runtime.health", "study_id": "DM002", "observed_at": "2026-05-09T00:59:00+00:00"}],
        "source_refs": [
            {
                "surface_kind": "runtime_health",
                "study_id": "DM002",
                "source_ref": "studies/DM002/artifacts/runtime/health/latest.json",
            }
        ],
    }
    conversation_payload = {
        "surface_kind": "mas_runtime_conversation_read_model",
        "selected_study_id": "DM002",
        "studies": [{"study_id": "DM002"}],
        "timeline": [
            {
                "study_id": "DM002",
                "item_kind": "user_message",
                "message_id": "msg-dm002",
                "source_ref": "studies/DM002/artifacts/runtime/user_message_queue.json",
            },
            {
                "study_id": "DM002",
                "item_kind": "turn_receipt",
                "run_id": "run-dm002",
                "tool_refs": [{"kind": "tool", "value": "study_progress"}],
                "source_ref": "studies/DM002/artifacts/runtime/turn_receipts/turn-001.json",
            }
        ],
        "source_refs": [
            {
                "surface_kind": "turn_receipts_jsonl",
                "source_ref": "studies/DM002/artifacts/runtime/turn_receipts/turn-001.json",
            }
        ],
    }
    console_ui_payload = {
        "selected_study_id": "DM002",
        "controller_action_intents": console_snapshot["controller_action_intents"],
        "terminal_attach_gate": {
            "surface_kind": "mas_terminal_attach_gate",
            "status": "blocked_by_missing_terminal_input_owner",
            "required_owner_contract": {
                "token": "MAS-issued attach token with explicit study/run scope and expiry",
                "lease": "single active terminal input lease with renewal and stale lease rejection",
                "idempotency": "dedupe key for each input, resize, and detach request",
                "audit": "append-only receipt for attach, input, resize, detach, denial, and expiry",
                "input": "MAS-owned terminal input route with authorization and run-state checks",
                "resize": "MAS-owned resize route with lease and run-state checks",
                "detach": "MAS-owned detach route with audited lease release",
            },
            "forbidden_owner": "legacy_mds_daemon_websocket",
            "read_only_default": True,
            "attach_started": False,
            "study_id": "DM002",
        },
        "source_refs": ["artifacts/runtime/live_console/session_read_model/latest.json"],
    }
    for path, payload in (
        (portal_payload_path, portal_payload),
        (study_page_payload, {"study_workbench": study_workbench}),
        (console_payload_path, console_snapshot),
        (console_ui_payload_path, console_ui_payload),
        (conversation_payload_path, conversation_payload),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_text(portal_html_path, "<!doctype html><title>Med Auto Science Progress Portal</title>")
    write_text(
        study_page_html,
        (
            "<!doctype html><title>Med Auto Science Study Workbench</title>"
            "<section><h2>研究路线地图</h2><svg class=\"route-map-svg\" aria-label=\"研究路线地图\">"
            "<g data-route-kind=\"route\"></g></svg></section>"
            "<h2>执行器对话</h2><ol class=\"conversation-timeline\">"
            "<li class=\"conversation-item conversation-item--user_message\" data-item-kind=\"user_message\"></li>"
            "<li class=\"conversation-item conversation-item--turn_receipt\" data-item-kind=\"turn_receipt\"></li>"
            "</ol><h3>对话来源</h3>"
        ),
    )
    write_text(console_html_path, "<!doctype html><title>Med Auto Science Live Console</title>")
    receipt_path = root / "artifacts" / "runtime" / "progress_portal" / "action_receipts" / "resume-001.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(
        json.dumps(
            {
                "surface_kind": "mas_progress_portal_action_receipt",
                "action": "resume",
                "study_id": "DM002",
                "quest_id": "DM002",
                "mode": "runtime_control_apply",
                "apply": True,
                "apply_status": "applied",
                "runtime_control_operation": "resume_quest",
                "forbidden_writes": [
                    "paper",
                    "package",
                    "publication_gate",
                    "controller_decision",
                    "controller_decisions/latest.json",
                    "runtime_sqlite_authority",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    report = module.build_portal_console_soak_report(
        profile=profile,
        portal_result={
            "status": "materialized",
            "payload_path": str(portal_payload_path),
            "html_path": str(portal_html_path),
            "hosted_package_path": str(root / "artifacts" / "runtime" / "progress_portal" / "hosted_package.json"),
            "study_pages": {
                "DM002": {
                    "payload_path": str(study_page_payload),
                    "html_path": str(study_page_html),
                    "html_ref": "ops/mas/progress/studies/DM002/index.html",
                }
            },
        },
        console_result={
            "status": "snapshot",
            "payload_path": str(console_payload_path),
            "history_path": str(root / "artifacts" / "runtime" / "live_console" / "session_read_model" / "history.jsonl"),
            "ui_payload_path": str(console_ui_payload_path),
            "html_path": str(console_html_path),
            "session_read_model": console_snapshot,
        },
        conversation_result={
            "status": "materialized",
            "payload_path": str(conversation_payload_path),
            "conversation_read_model": conversation_payload,
        },
        generated_at="2026-05-09T01:00:00+00:00",
    )

    assert report["status"] == "passed"
    assert set(report["evidence"]) == {
        "portal_refresh",
        "per_study_workbench",
        "route_map_visualization",
        "route_decision_trail",
        "per_study_deep_link",
        "conversation_read_model",
        "conversation_portal_panel",
        "study_scoped_console",
        "action_receipts",
        "authorized_action_apply_receipts",
        "terminal_attach_gate",
        "latency_slo_source_refs",
        "live_console_study_run_disambiguation",
        "terminal_log_refs",
        "source_ref_cleanliness",
        "product_identity",
        "write_boundary",
    }
    assert report["evidence"]["per_study_workbench"]["status"] == "passed"
    assert report["evidence"]["route_map_visualization"]["status"] == "passed"
    assert report["evidence"]["route_map_visualization"]["node_kinds"] == ["decision", "route", "stage"]
    assert report["evidence"]["route_map_visualization"]["edge_kinds"] == ["advance"]
    assert report["evidence"]["route_decision_trail"]["active_paths"] == ["analysis-route-b"]
    assert report["evidence"]["conversation_read_model"]["timeline_kinds"] == ["turn_receipt", "user_message"]
    assert set(report["evidence"]["conversation_read_model"]["source_refs"]) == {
        "studies/DM002/artifacts/runtime/user_message_queue.json",
        "studies/DM002/artifacts/runtime/turn_receipts/turn-001.json",
    }
    assert report["evidence"]["conversation_portal_panel"]["status"] == "passed"
    assert report["evidence"]["conversation_portal_panel"]["timeline_kinds"] == ["turn_receipt", "user_message"]
    assert report["evidence"]["action_receipts"]["direct_execution_intents"] == []
    assert report["evidence"]["authorized_action_apply_receipts"]["applied_actions"] == ["resume"]
    assert report["evidence"]["terminal_attach_gate"]["status"] == "passed"
    assert report["evidence"]["terminal_attach_gate"]["attach_started"] is False
    assert report["authority"]["controller_action_execution_allowed"] is False


def test_portal_console_soak_blocks_when_user_parity_evidence_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.portal_console_soak")
    profile = make_profile(tmp_path)
    root = profile.workspace_root
    portal_payload_path = root / "artifacts" / "runtime" / "progress_portal" / "latest.json"
    portal_html_path = root / "ops" / "mas" / "progress" / "index.html"
    console_payload_path = root / "artifacts" / "runtime" / "live_console" / "session_read_model" / "latest.json"
    console_ui_payload_path = root / "artifacts" / "runtime" / "live_console" / "ui_payload" / "latest.json"
    console_html_path = root / "ops" / "mas" / "live-console" / "index.html"

    for path, payload in (
        (
            portal_payload_path,
            {
                "generated_at": "2026-05-09T01:00:00+00:00",
                "workspace": {"studies": [{"study_id": "DM002"}]},
                "source_refs": ["studies/DM002/artifacts/runtime/health/latest.json"],
            },
        ),
        (
            console_payload_path,
            {
                "selected_study_id": None,
                "studies": [{"study_id": "DM002", "runs": []}],
                "stream_sources": [],
                "controller_action_intents": [],
                "source_refs": [],
            },
        ),
        (console_ui_payload_path, {"source_refs": []}),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_text(portal_html_path, "<!doctype html><title>Med Auto Science Progress Portal</title>")
    write_text(console_html_path, "<!doctype html><title>Med Auto Science Live Console</title>")

    report = module.build_portal_console_soak_report(
        profile=profile,
        portal_result={
            "status": "materialized",
            "payload_path": str(portal_payload_path),
            "html_path": str(portal_html_path),
            "hosted_package_path": str(root / "artifacts" / "runtime" / "progress_portal" / "hosted_package.json"),
        },
        console_result={
            "status": "snapshot",
            "payload_path": str(console_payload_path),
            "history_path": str(root / "artifacts" / "runtime" / "live_console" / "session_read_model" / "history.jsonl"),
            "ui_payload_path": str(console_ui_payload_path),
            "html_path": str(console_html_path),
        },
        conversation_result={},
        generated_at="2026-05-09T01:00:00+00:00",
    )

    assert report["status"] == "blocked"
    assert report["evidence"]["per_study_workbench"]["blockers"] == ["missing_per_study_sections_or_pages"]
    assert report["evidence"]["per_study_deep_link"]["blockers"] == [
        "missing_study_scoped_portal_or_console_deep_link"
    ]
    assert "missing_route_decision_trail_surface" in report["evidence"]["route_decision_trail"]["blockers"]
    assert "missing_route_nodes" in report["evidence"]["route_decision_trail"]["blockers"]
    assert "missing_route_map_surface" in report["evidence"]["route_map_visualization"]["blockers"]
    assert "missing_conversation_read_model" in report["evidence"]["conversation_read_model"]["blockers"]
    assert "missing_conversation_portal_panel" in report["evidence"]["conversation_portal_panel"]["blockers"]
    assert "missing_selected_study_id" in report["evidence"]["study_scoped_console"]["blockers"]
    assert "missing_terminal_attach_gate" in report["evidence"]["terminal_attach_gate"]["blockers"]
