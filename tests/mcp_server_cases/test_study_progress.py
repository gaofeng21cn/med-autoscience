from __future__ import annotations

import importlib
from pathlib import Path

from med_autoscience.controllers.study_progress import projection as study_progress_projection
from tests.mcp_server_cases.profile import write_profile
from tests.mcp_server_cases.result_envelope import _assert_tool_result_envelope, _structured_payload

def test_mcp_default_status_progress_does_not_require_external_mds_repo(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text(
        "\n".join(
            [
                "study_id: 001-risk",
                "execution:",
                "  auto_entry: on_managed_research_intent",
                "  quest_id: quest-001",
                "  opl_runtime_ref: opl_hosted_stage_runtime",
                "  runtime_ref: opl_hosted_stage_runtime",
                "  runtime_engine_id: opl-hosted-stage-runtime",
                "  research_backend_id: mas_domain_intent_adapter",
                "  research_backend: mas_domain_intent_adapter",
                "  research_engine_id: mas-domain-intent-adapter",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    profile_path = tmp_path / "profile.local.toml"
    profile_path.write_text(
        "\n".join(
            [
                'name = "minimal"',
                f'workspace_root = "{workspace_root}"',
                f'runtime_root = "{workspace_root / "runtime" / "quests"}"',
                f'studies_root = "{workspace_root / "studies"}"',
                f'portfolio_root = "{workspace_root / "memory" / "portfolio"}"',
                f'med_deepscientist_runtime_root = "{workspace_root / "runtime"}"',
                'med_deepscientist_repo_root = ""',
                f'hermes_agent_repo_root = "{tmp_path / "_external" / "hermes-agent"}"',
                f'hermes_home_root = "{tmp_path / ".hermes"}"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    progress_result = module.call_tool(
        "study_progress",
        {
            "profile_path": str(profile_path),
            "study_id": "001-risk",
        },
    )

    _assert_tool_result_envelope(progress_result, tool_id="study_progress")
    assert progress_result["isError"] is False
    progress_payload = _structured_payload(progress_result)
    assert progress_payload["quest_root"] == str(workspace_root / "runtime" / "quests" / "quest-001")
    assert progress_payload["authority_snapshot"]["canonical_runtime_action"]
def test_mcp_server_progress_projection_prefers_progress_projection_markdown_when_available(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    monkeypatch.setattr(
        study_progress_projection,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": "001-risk",
            "current_stage": "publication_supervision",
            "current_stage_summary": "当前已有论文包雏形，但真正的硬阻塞仍在论文可发表性面。",
            "paper_stage": "publishability_gate_blocked",
            "paper_stage_summary": "当前关键路径是补齐论文证据与叙事，而不是抢跑打包。",
            "current_blockers": ["缺少最小投稿包导出。"],
            "latest_events": [],
            "next_system_action": "先补齐论文证据与叙事，再回到发表门控复核。",
            "study_macro_state": {
                "surface": "study_macro_state",
                "schema_version": 1,
                "study_id": "001-risk",
                "writer_state": "live",
                "user_next": "watch",
                "reason": "runtime",
                "details": {"active_run_id": "run-001", "package_delivered": False},
                "conditions": [],
            },
            "user_visible_projection": {
                "surface": "study_progress_user_visible_projection",
                "schema_version": 2,
                "authority": "truth_projection",
                "projection_only": True,
                "study_id": "001-risk",
                "state": "live/watch/runtime",
                "writer_state": "live",
                "user_next": "watch",
                "reason": "runtime",
                "package_delivered": False,
                "actual_write_active": True,
                "user_action_required": False,
                "state_label": "自动运行中",
                "state_summary": "当前已有论文包雏形，但真正的硬阻塞仍在论文可发表性面。",
                "current_stage": "live",
                "current_stage_summary": "当前已有论文包雏形，但真正的硬阻塞仍在论文可发表性面。",
                "paper_stage": "publishability_gate_blocked",
                "paper_stage_summary": "当前关键路径是补齐论文证据与叙事，而不是抢跑打包。",
                "current_blockers": ["缺少最小投稿包导出。"],
                "next_system_action": "先补齐论文证据与叙事，再回到发表门控复核。",
                "evidence": {"latest_events": [], "refs": {}},
                "conditions": [],
            },
            "auto_runtime_parked": {
                "surface_kind": "auto_runtime_parked",
                "parked": False,
                "source_reason": "quest_already_running",
            },
            "needs_physician_decision": False,
            "task_intake": {
                "study_id": "001-risk",
                "task_intent": "reviewer revision",
                "submission_revision_operating_contract": {"large": "detail"},
            },
            "runtime_efficiency": {
                "run_id": "run-001",
                "latest_evidence_packets": [{"payload": "large"}],
                "evidence_packet_count": 1,
            },
            "supervision": {
                "browser_url": "http://127.0.0.1:21001",
                "quest_session_api_url": "http://127.0.0.1:21001/api/session",
                "active_run_id": "run-001",
                "launch_report_path": "/tmp/studies/001-risk/artifacts/runtime/last_launch_report.json",
            },
        },
    )

    result = module.call_tool(
        "study_progress",
        {
            "profile_path": str(profile_path),
            "study_id": "001-risk",
        },
    )

    assert result["isError"] is False
    _assert_tool_result_envelope(result, tool_id="study_progress")
    projection = _structured_payload(result)
    assert projection["study_id"] == "001-risk"
    assert projection["mcp_projection"]["compacted"] is True
    assert projection["task_intake"]["task_intent"] == "reviewer revision"
    assert "submission_revision_operating_contract" not in projection["task_intake"]
    assert "latest_evidence_packets" not in projection["runtime_efficiency"]
    assert "# 研究进度" in result["content"][0]["text"]
    assert "论文可发表性面" in result["content"][0]["text"]
    assert "parked: `False`" in result["content"][0]["text"]
    assert "auto_runtime_parked" not in result["content"][0]["text"]
def test_mcp_server_can_call_study_progress_tool(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    captured: dict[str, object] = {}

    def fake_read_study_progress(**kwargs):
        captured.update(kwargs)
        return {
            "study_id": "001-risk",
            "current_stage": "managed_runtime_active",
            "current_stage_summary": "托管运行时正在自动推进研究。",
            "current_blockers": [f"blocker-{index}" for index in range(20)],
            "study_macro_state": {
                "surface": "study_macro_state",
                "schema_version": 1,
                "study_id": "001-risk",
                "writer_state": "live",
                "user_next": "watch",
                "reason": "runtime",
                "details": {"active_run_id": "run-001", "package_delivered": False},
                "conditions": [],
            },
            "user_visible_projection": {
                "surface": "study_progress_user_visible_projection",
                "schema_version": 2,
                "authority": "truth_projection",
                "projection_only": True,
                "study_id": "001-risk",
                "state": "live/watch/runtime",
                "writer_state": "live",
                "user_next": "watch",
                "reason": "runtime",
                "package_delivered": False,
                "actual_write_active": True,
                "user_action_required": False,
                "state_label": "自动运行中",
                "state_summary": "托管运行时正在自动推进研究。",
                "current_stage": "live",
                "current_stage_summary": "托管运行时正在自动推进研究。",
                "current_blockers": [f"blocker-{index}" for index in range(20)],
                "next_system_action": "观察自动运行推进。",
                "evidence": {"latest_events": [], "refs": {}},
                "conditions": [],
            },
            "task_intake": {
                "study_id": "001-risk",
                "task_intent": "reviewer revision",
                "constraints": [f"constraint-{index}" for index in range(20)],
                "submission_revision_operating_contract": {"large": "detail"},
            },
            "runtime_efficiency": {
                "run_id": "run-001",
                "evidence_packet_count": 22,
                "latest_evidence_packets": [{"payload": "large"}],
            },
            "progress_first_monitoring_summary": {
                "surface": "progress_first_monitoring_summary",
                "authority": "refs_only_observability",
                "study_id": "001-risk",
                "active_run_id": "run-001",
                "active_stage_attempt_id": "stage-attempt-001",
                "active_workflow_id": "workflow-001",
                "running_provider_attempt": True,
                "worker_liveness": {"health_status": "live"},
                "execution_state_kind": "running_provider_attempt",
                "next_owner": "mas_controller",
                "controller_action": "run_quality_repair_batch",
                "next_work_unit": {
                    "unit_id": "quality_repair_batch",
                    "summary": "Repair paper evidence.",
                },
                "stage_progress_log": {
                    "attempt_count": 1,
                    "completed_attempt_count": 0,
                    "blocked_attempt_count": 0,
                    "runner_progress_event_count": 3,
                    "attempt_refs": [f"attempt-ref-{index}" for index in range(10)],
                },
                "latest_terminal_stage": {
                    "action_type": "run_quality_repair_batch",
                    "status": "blocked",
                    "outcome": "typed_blocker",
                    "remaining_blockers": ["current package stale"],
                    "evidence_refs": ["/tmp/evidence.json"],
                },
                "foreground_write_policy": {
                    "supervisor_only": True,
                    "foreground_can_write_runtime_owned_surfaces": False,
                },
                "authority_boundary": {
                    "refs_only": True,
                    "can_write_runtime_owned_surfaces": False,
                    "can_write_paper_or_package": False,
                },
            },
        }

    monkeypatch.setattr(study_progress_projection, "read_study_progress", fake_read_study_progress)

    result = module.call_tool(
        "study_progress",
        {
            "profile_path": str(profile_path),
            "study_id": "001-risk",
        },
    )

    assert result["isError"] is False
    _assert_tool_result_envelope(result, tool_id="study_progress")
    assert captured["sync_runtime_summary"] is False
    assert captured["materialize_read_model_artifacts"] is False
    payload = _structured_payload(result)
    assert payload["study_id"] == "001-risk"
    assert payload["current_stage"] == "live"
    assert payload["state_label"] == "自动运行中"
    assert payload["mcp_projection"]["compacted"] is True
    assert payload["mcp_projection"]["projection_only"] is True
    assert payload["mcp_projection"]["authority"] is False
    assert payload["mcp_projection"]["can_generate_action"] is False
    assert payload["mcp_projection"]["can_execute"] is False
    assert payload["mcp_projection"]["source_truth_required"] == "canonical_next_action_or_paper_mission_readback"
    assert payload["mcp_projection"]["diagnostic_source_refs"] == ["current_owner_delta", "opl_readback"]
    assert payload["current_blockers"][-1] == "blocker-11"
    assert len(payload["task_intake"]["constraints"]) == 8
    assert "submission_revision_operating_contract" not in payload["task_intake"]
    assert "latest_evidence_packets" not in payload["runtime_efficiency"]
    monitoring = payload["progress_first_monitoring_summary"]
    assert monitoring["active_run_id"] == "run-001"
    assert monitoring["active_stage_attempt_id"] == "stage-attempt-001"
    assert monitoring["worker_liveness"]["health_status"] == "live"
    assert monitoring["next_owner"] == "mas_controller"
    assert monitoring["controller_action"] == "run_quality_repair_batch"
    assert monitoring["next_work_unit"]["unit_id"] == "quality_repair_batch"
    assert monitoring["stage_progress_log"]["attempt_count"] == 1
    assert monitoring["stage_progress_log"]["attempt_refs"][-1] == "attempt-ref-5"
    assert monitoring["latest_terminal_stage"]["remaining_blockers"] == ["current package stale"]
    assert monitoring["foreground_write_policy"]["foreground_can_write_runtime_owned_surfaces"] is False
    assert monitoring["authority_boundary"]["can_write_paper_or_package"] is False
    assert "## Progress-First Monitoring" in result["content"][0]["text"]
    assert "自动推进研究" in result["content"][0]["text"]
