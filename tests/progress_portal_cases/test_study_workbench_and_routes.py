from __future__ import annotations

import importlib
import json

from tests.progress_portal_cases.helpers import _progress_payload


def test_study_workbench_helper_projects_path_stage_artifacts_and_source_refs_without_filename_inference() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")

    payload = parts.build_study_workbench_payload(
        progress={
            **_progress_payload(),
            "route_decision_trail": {
                "active_path": "analysis-route-b",
                "winning_path": "analysis-route-b",
                "nodes": [
                    {
                        "route_id": "analysis-route-a",
                        "label": "Start with broad risk model",
                        "evidence_point": "calibration audit",
                        "blocked_reason": "external validation failed",
                        "pivot_rationale": "route B has transportable subgroup evidence",
                        "superseded_by": "analysis-route-b",
                    }
                ],
                "source_refs": ["studies/001-risk/artifacts/controller_decisions/latest.json"],
            },
            "artifact_locators": [
                {
                    "group": "draft",
                    "label": "canonical manuscript draft",
                    "ref": "studies/001-risk/paper/manuscript.md",
                    "status": "fresh",
                },
                {
                    "category": "review_proof",
                    "label": "AI reviewer proof",
                    "path": "studies/001-risk/artifacts/publication_eval/latest.json",
                    "status": "blocked",
                },
                {
                    "label": "looks like a figure but has no explicit group",
                    "ref": "studies/001-risk/manuscript/current_package/figures/Figure1.png",
                },
            ],
            "delivery_refs": [
                {
                    "kind": "figures_tables",
                    "label": "Table 1",
                    "ref": "studies/001-risk/paper/tables/table1.csv",
                }
            ],
        },
        cockpit={
            "studies": [
                {
                    "study_id": "001-risk",
                    "current_stage": "cockpit-stage",
                    "paper_stage": "cockpit-paper-stage",
                    "monitoring": {"health_status": "recovering"},
                }
            ]
        },
        runtime={
            "study_id": "001-risk",
            "active_run_id": "run-001",
            "artifact_locators": [
                {
                    "group": "runtime_evidence",
                    "label": "runtime supervision",
                    "ref": "studies/001-risk/artifacts/runtime/runtime_supervision/latest.json",
                }
            ],
        },
        package={
            "study_id": "001-risk",
            "refs": [
                "studies/001-risk/manuscript/current_package",
                "studies/001-risk/manuscript/current_package.zip",
            ],
        },
        study_id="001-risk",
    )

    assert payload["surface_kind"] == "mas_progress_portal_study_workbench"
    tabs_by_id = {item["id"]: item for item in payload["tabs"]}
    assert tabs_by_id["route_map"] == {"id": "route_map", "label": "研究路线地图", "status": "available"}
    assert tabs_by_id["route_decision_trail"] == {"id": "route_decision_trail", "label": "路线/决策", "status": "available"}
    assert payload["route_decision_trail"]["surface_kind"] == "mas_progress_portal_route_decision_trail"
    assert payload["route_decision_trail"]["active_path"] == "analysis-route-b"
    assert payload["route_decision_trail"]["winning_path"] == "analysis-route-b"
    assert {key: payload["route_decision_trail"]["nodes"][0].get(key) for key in ("route_id", "label", "decision", "evidence_point", "blocked_reason", "pivot_rationale", "superseded_by", "source")} == {
        "route_id": "analysis-route-a",
        "label": "Start with broad risk model",
        "decision": None,
        "evidence_point": "calibration audit",
        "blocked_reason": "external validation failed",
        "pivot_rationale": "route B has transportable subgroup evidence",
        "superseded_by": "analysis-route-b",
        "source": "route_decision_trail.nodes",
    }
    assert payload["route_decision_trail"]["authority"]["writes_authority_surface"] is False
    assert payload["route_decision_trail"]["authority"]["forbidden_authority"] == [
        "study_truth",
        "publication_judgment",
        "quality_verdict",
        "runtime_authority",
        "artifact_authority",
        "controller_decision_authority",
    ]
    assert payload["route_map"]["surface_kind"] == "mas_progress_portal_route_map"
    assert payload["route_map"]["status"] == "available"
    assert {node["kind"] for node in payload["route_map"]["nodes"]} >= {"stage", "route", "decision", "blocker"}
    assert any(edge["kind"] == "blocked" for edge in payload["route_map"]["edges"])
    assert payload["route_map"]["authority"]["writes_authority_surface"] is False
    assert payload["path_stage"]["current_stage"] == "quality_repair"
    assert payload["path_stage"]["paper_stage"] == "revision"
    assert payload["runtime"]["active_run_id"] == "run-001"
    assert payload["artifact_groups"]["draft"]["items"][0]["ref"] == "studies/001-risk/paper/manuscript.md"
    assert payload["artifact_groups"]["figures_tables"]["items"][0]["ref"] == "studies/001-risk/paper/tables/table1.csv"
    assert payload["artifact_groups"]["current_package"]["items"] == [
        {
            "ref": "studies/001-risk/manuscript/current_package",
            "label": "studies/001-risk/manuscript/current_package",
            "status": "available",
            "source": "package.refs",
        },
        {
            "ref": "studies/001-risk/manuscript/current_package.zip",
            "label": "studies/001-risk/manuscript/current_package.zip",
            "status": "available",
            "source": "package.refs",
        },
    ]
    assert payload["artifact_groups"]["review_proof"]["items"][0]["status"] == "blocked"
    assert payload["artifact_groups"]["runtime_evidence"]["items"][0]["ref"].endswith(
        "runtime_supervision/latest.json"
    )
    all_refs = [
        item["ref"]
        for group in payload["artifact_groups"].values()
        for item in group["items"]
    ]
    assert "studies/001-risk/manuscript/current_package/figures/Figure1.png" not in all_refs
    assert "artifact_group:draft" not in payload["conditions"]["missing"]
    assert "artifact_group:figures_tables" not in payload["conditions"]["missing"]
    assert "artifact_group:current_package" not in payload["conditions"]["missing"]
    assert "artifact_group:review_proof" not in payload["conditions"]["missing"]
    assert "artifact_group:runtime_evidence" not in payload["conditions"]["missing"]
    assert "studies/001-risk/artifacts/controller_decisions/latest.json" in payload["source_refs"]
    assert tabs_by_id["artifacts"] == {"id": "artifacts", "label": "产物", "status": "available"}


def test_study_workbench_projects_progress_first_next_delta_for_operator_visibility() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")
    progress = {
        **_progress_payload(),
        "deliverable_progress_delta": {"count": 0, "token_usage_total": 0},
        "paper_progress_delta": {"count": 0, "token_usage_total": 0},
        "platform_repair_delta": {"count": 1, "token_usage_total": 2048},
        "progress_delta_classification": "platform_repair",
        "progress_first_sprint_state": {
            "classification": "platform_repair",
            "paper_progress_delta_counted": False,
            "platform_repair_delta_counted": True,
            "deliverable_progress_delta": {"count": 0, "token_usage_total": 0},
            "paper_progress_delta": {"count": 0, "token_usage_total": 0},
            "platform_repair_delta": {"count": 1, "token_usage_total": 2048},
        },
        "next_forced_delta": {
            "required_delta_kind": "paper_progress_delta_or_typed_blocker",
            "reason": "platform_repair_does_not_count_as_paper_progress",
            "work_unit_id": "publishability_repair_sprint",
            "target_surface": {
                "ref_kind": "route_obligation",
                "route_target": "write",
                "surface_ref": "canonical_manuscript",
            },
            "acceptance_refs": [
                "canonical_manuscript_delta",
                "ai_reviewer_gate_replay_request",
            ],
            "owner_action": {
                "next_owner": "runtime_mechanism_repair",
                "work_unit_id": "publishability_repair_sprint",
                "allowed_actions": ["paper_autonomy/repair-recheck"],
                "owner_receipt_required": True,
            },
        },
    }

    payload = parts.build_study_workbench_payload(
        progress=progress,
        cockpit={},
        runtime={"study_id": "001-risk", "active_run_id": "run-001"},
        package={"study_id": "001-risk"},
        study_id="001-risk",
    )
    html = parts.render_study_workbench_sections(payload)

    tabs_by_id = {item["id"]: item for item in payload["tabs"]}
    assert tabs_by_id["progress_first"] == {
        "id": "progress_first",
        "label": "Progress-First",
        "status": "available",
    }
    projection = payload["progress_first"]
    assert projection["status"] == "available"
    assert projection["progress_delta_classification"] == "platform_repair"
    assert projection["deliverable_progress_delta"]["count"] == 0
    assert projection["paper_progress_delta"]["count"] == 0
    assert projection["platform_repair_delta"]["count"] == 1
    assert projection["platform_repair_is_deliverable_progress"] is False
    assert projection["next_forced_delta"]["required_delta_kind"] == "paper_progress_delta_or_typed_blocker"
    assert projection["next_forced_delta"]["target_surface"]["surface_ref"] == "canonical_manuscript"
    assert projection["next_forced_delta"]["acceptance_refs"] == [
        "canonical_manuscript_delta",
        "ai_reviewer_gate_replay_request",
    ]
    assert projection["next_forced_delta"]["owner_action"]["next_owner"] == "runtime_mechanism_repair"
    assert projection["authority"]["writes_authority_surface"] is False
    assert projection["authority"]["can_authorize_quality_verdict"] is False
    assert "Progress-First" in html
    assert "paper_progress_delta_or_typed_blocker" in html
    assert "platform_repair_delta=1" in html


def test_study_workbench_progress_first_exposes_canonical_current_work_unit() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")
    progress = {
        **_progress_payload(),
        "progress_first_monitoring_summary": {
            "surface": "progress_first_monitoring_summary",
            "schema_version": 1,
            "authority": "refs_only_observability",
            "study_id": "001-risk",
            "running_provider_attempt": False,
            "execution_state_kind": "executable_owner_action",
            "owner_action_current": True,
            "next_owner": "ai_reviewer",
            "controller_action": "return_to_ai_reviewer_workflow",
            "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "executable_owner_action",
                "owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "sha256:current-work-unit",
                "state": {
                    "state_kind": "executable_owner_action",
                    "provider_admission_pending": True,
                },
            },
        },
    }

    payload = parts.build_study_workbench_payload(
        progress=progress,
        cockpit={},
        runtime={"study_id": "001-risk", "active_run_id": "run-001"},
        package={"study_id": "001-risk"},
        study_id="001-risk",
    )
    html = parts.render_study_workbench_sections(payload)
    projection = payload["progress_first"]

    assert projection["current_work_unit"]["work_unit_id"] == (
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    assert projection["current_work_unit"]["status"] == "executable_owner_action"
    assert projection["current_work_unit"]["state"]["provider_admission_pending"] is True
    assert "produce_ai_reviewer_publication_eval_record_against_current_inputs" in html
    assert "admission_pending=True" in html


def test_study_workbench_helper_does_not_accept_runtime_conversation_read_model() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")
    portal_module = importlib.import_module("med_autoscience.controllers.progress_portal")
    rendering = importlib.import_module("med_autoscience.controllers.progress_portal_parts.rendering")

    payload = parts.build_study_workbench_payload(
        progress=_progress_payload(),
        cockpit={},
        runtime={"study_id": "001-risk", "active_run_id": "run-001"},
        package={"study_id": "001-risk"},
        study_id="001-risk",
    )
    html = parts.render_study_workbench_sections(payload)
    portal_html = portal_module.render_progress_portal_html(
        portal_module.build_progress_portal_payload(
            profile_name="diabetes",
            workspace_root="/workspace",
            study_id="001-risk",
            progress_payload=_progress_payload(),
            runtime_payload={
                "study_id": "001-risk",
                "runtime_conversation_read_model": {
                    "messages": [
                        {"role": "user", "content": "confirm next route"},
                    ],
                },
            },
            generated_at="2026-05-08T01:05:00+00:00",
        )
    )
    portal_css = rendering.portal_css()

    assert all(tab["id"] != "conversation" for tab in payload["tabs"])
    assert "conversation" not in payload
    assert "执行器对话" not in html
    assert "执行器对话" not in portal_html
    assert "runtime_conversation_read_model" not in json.dumps(payload, ensure_ascii=False)
    assert "runtime_conversation_read_model" not in portal_html
    assert "conversation-" not in portal_css
    assert "共 4 条" not in html
    assert "用户消息" not in html
    assert "用户消息" not in portal_html
    assert "msg-pending" not in html
    assert "执行回合" not in html
    assert "confirm next route" not in portal_html
    assert "run-001" in html
    assert "blocked_waiting_for_user" not in html
    assert "confirm next route" not in html
    assert "runtime/quests/001/artifacts/runtime/turn_receipts.jsonl" not in html
    assert "run-other" not in html


def test_study_workbench_helper_fail_closes_missing_inputs_and_conflicts() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")

    payload = parts.build_study_workbench_payload(
        progress={},
        cockpit={"studies": [{"study_id": "other-study"}]},
        runtime={"study_id": "other-study"},
        package={"study_id": "other-study"},
        study_id="001-risk",
    )

    assert payload["overview"]["state_label"] is None
    assert payload["path_stage"]["current_stage"] is None
    assert payload["source_refs"] == []
    assert payload["artifact_groups"]["draft"]["status"] == "missing"
    assert payload["artifact_groups"]["current_package"]["status"] == "missing"
    assert payload["conditions"]["missing"] == [
        "study_progress",
        "user_visible_projection_v2",
        "source_refs",
        "runtime_active_run_id",
        "artifact_group:draft",
        "artifact_group:figures_tables",
        "artifact_group:current_package",
        "artifact_group:review_proof",
        "artifact_group:runtime_evidence",
        "route_decision_trail:route_decision_trail",
        "route_decision_trail:route_nodes",
        "stage_knowledge_visibility",
        "stage_knowledge:missing_study_root_for_stage_knowledge_visibility",
    ]
    assert payload["conditions"]["conflict"] == [
        "runtime_study_id_mismatch",
        "package_study_id_mismatch",
        "cockpit_study_id_mismatch",
    ]
    assert "conversation" not in payload


def test_study_workbench_render_helper_returns_html_sections() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")
    payload = parts.build_study_workbench_payload(
        progress=_progress_payload(),
        cockpit={},
        runtime={"study_id": "001-risk", "active_run_id": "run-001"},
        package={"study_id": "001-risk", "refs": ["studies/001-risk/manuscript/current_package.zip"]},
        study_id="001-risk",
    )

    html = parts.render_study_workbench_sections(payload)

    assert "单篇论文工作台" in html
    assert "路线 / 决策" in html
    assert "缺少显式路线节点" in html
    assert "路径与阶段" in html
    assert "当前交付包" in html
    assert "studies/001-risk/manuscript/current_package.zip" in html
    assert "缺少 source refs。" not in html


def test_route_decision_trail_helper_projects_branch_block_pivot_and_winning_path() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")

    payload = parts.build_route_decision_trail_payload(
        progress={
            "study_id": "001-risk",
            "controller_decision": {
                "decision_type": "study_line_route_decision",
                "route_decision": "switch_line",
                "route_target": "route-b",
                "selected_line_id": "route-b",
                "route_rationale": "route A blocked at validation; route B preserves the claim boundary.",
                "blockers": ["route-a_external_validation_failed"],
                "candidate_path_graph": {
                    "surface": "candidate_path_graph",
                    "authority": "read_model_only",
                    "selected_candidate_id": "route-b",
                    "candidates": [
                        {
                            "candidate_id": "route-a",
                            "question": "Can broad model generalize?",
                            "decision": "stop",
                            "evidence_basis": ["external validation AUC dropped"],
                            "stop_rule": "stop if external validation fails",
                        },
                        {
                            "candidate_id": "route-b",
                            "question": "Can subgroup route preserve the claim?",
                            "decision": "pivot",
                            "evidence_basis": ["subgroup signal replicated"],
                            "expected_artifact": "artifacts/medical_paper/candidate_paths/route-b.json",
                        },
                    ],
                    "source_refs": ["studies/001-risk/artifacts/medical_paper/route_decision_orchestrator.json"],
                },
                "source_refs": ["studies/001-risk/artifacts/controller_decisions/latest.json"],
            },
        },
        runtime={},
        package={},
        study_id="001-risk",
    )

    assert payload["status"] == "available"
    assert payload["active_path"] == "route-b"
    assert payload["winning_path"] == "route-b"
    assert [node["route_id"] for node in payload["nodes"]] == ["route-a", "route-b"]
    assert payload["nodes"][0]["blocked_reason"] == "stop if external validation fails"
    assert payload["nodes"][0]["pivot_rationale"] == "route A blocked at validation; route B preserves the claim boundary."
    assert payload["nodes"][1]["decision"] == "pivot"
    assert "studies/001-risk/artifacts/controller_decisions/latest.json" in payload["source_refs"]
    html = parts.render_route_decision_trail_section(payload)
    assert "路线 / 决策" in html
    assert "当前路线：route-b" in html
    assert "当前采用：route-b" in html
    assert "route-a" in html
    assert "阻塞=stop if external validation fails" in html
    assert "路线来源" in html
    assert "studies/001-risk/artifacts/controller_decisions/latest.json" in html


def test_route_decision_trail_helper_fail_closes_without_explicit_route_inputs() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")

    payload = parts.build_route_decision_trail_payload(
        progress={
            "study_id": "001-risk",
            "artifact_locators": [
                {
                    "group": "draft",
                    "ref": "studies/001-risk/manuscript/current_package/route-a-wins.txt",
                }
            ],
        },
        runtime={},
        package={},
        study_id="001-risk",
    )

    assert payload["status"] == "missing"
    assert payload["nodes"] == []
    assert payload["active_path"] is None
    assert payload["conditions"]["missing"] == ["route_decision_trail", "route_nodes"]
    assert payload["source_refs"] == []


def test_route_decision_trail_helper_blocks_incomplete_explicit_route_inputs() -> None:
    parts = importlib.import_module("med_autoscience.controllers.progress_portal_parts")

    payload = parts.build_route_decision_trail_payload(
        progress={
            "study_id": "001-risk",
            "route_decision_trail": {
                "surface_kind": "mas_progress_portal_route_decision_trail",
                "nodes": [
                    {
                        "route_id": "route-a",
                        "label": "Can broad model generalize?",
                        "decision": "continue",
                    }
                ],
            },
        },
        runtime={},
        package={},
        study_id="001-risk",
    )

    assert payload["status"] == "missing"
    assert [node["route_id"] for node in payload["nodes"]] == ["route-a"]
    assert payload["conditions"]["missing"] == [
        "active_path",
        "winning_path",
        "route_source_refs",
    ]
