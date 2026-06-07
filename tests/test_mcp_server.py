from __future__ import annotations

import builtins
import importlib
import sys
from pathlib import Path

import pytest

from tests.mcp_server_cases.delivery_inspection_visibility import *
from tests.mcp_server_cases.open_auto_research_projection import *

EXPECTED_MCP_TOOLS = [
    "doctor_audit",
    "workspace_readiness",
    "research_assets",
    "study_progress",
    "open_auto_research_soak",
    "publication_status",
    "authority_operations",
]


def test_mcp_server_tool_registry_import_is_lightweight(monkeypatch: pytest.MonkeyPatch) -> None:
    original_import = builtins.__import__
    blocked_roots = {"pypdf", "matplotlib"}

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):  # type: ignore[no-untyped-def]
        if name.split(".", 1)[0] in blocked_roots:
            raise ModuleNotFoundError(f"No module named {name!r}")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    sys.modules.pop("med_autoscience.mcp_server", None)

    module = importlib.import_module("med_autoscience.mcp_server")

    assert [tool["name"] for tool in module.list_tools()] == EXPECTED_MCP_TOOLS


def write_profile(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                'name = "nfpitnet"',
                'workspace_root = "/Users/gaofeng/workspace/Yang/NF-PitNET"',
                'runtime_root = "/Users/gaofeng/workspace/Yang/NF-PitNET/runtime/quests"',
                'studies_root = "/Users/gaofeng/workspace/Yang/NF-PitNET/studies"',
                'portfolio_root = "/Users/gaofeng/workspace/Yang/NF-PitNET/portfolio"',
                'med_deepscientist_runtime_root = "/Users/gaofeng/workspace/Yang/NF-PitNET/runtime"',
                'med_deepscientist_repo_root = ""',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "enable_medical_overlay = true",
                'medical_overlay_scope = "workspace"',
                'medical_overlay_skills = ["scout", "idea", "decision", "write", "finalize"]',
                'research_route_bias_policy = "high_plasticity_medical"',
                'preferred_study_archetypes = ["clinical_classifier", "clinical_subtype_reconstruction", "external_validation_model_update", "gray_zone_triage", "llm_agent_clinical_task", "mechanistic_sidecar_extension"]',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_mcp_server_lists_read_only_tools() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")

    tools = module.list_tools()
    names = [tool["name"] for tool in tools]

    assert names == EXPECTED_MCP_TOOLS


@pytest.mark.parametrize(
    "fragment",
    (
        "workspace_authority_migration_audit",
        "storage_governance_report",
        "delivery_authority_backfill_apply",
        "artifact_lifecycle_report",
        "dry-run",
        "Physical cleanup and safe-cache deletion are owned by OPL",
    ),
)
def test_mcp_authority_operations_description_documents_authority_operation_surfaces(fragment: str) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    tools = {tool["name"]: tool for tool in module.build_tool_manifest()}

    assert fragment in tools["authority_operations"]["description"]


@pytest.mark.parametrize(
    ("option", "schema"),
    (
        ("apply", {"type": "boolean"}),
        ("markdown", {"type": "boolean"}),
        ("deep", {"type": "boolean"}),
        ("max_files", {"type": "integer", "minimum": 1}),
        ("max_seconds", {"type": "number", "exclusiveMinimum": 0}),
        ("authority_snapshot", {"type": "object"}),
    ),
)
def test_mcp_authority_operations_schema_accepts_authority_operation_options(
    option: str,
    schema: dict[str, object],
) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    tools = {tool["name"]: tool for tool in module.build_tool_manifest()}
    properties = tools["authority_operations"]["inputSchema"]["properties"]

    assert properties[option] == schema


def test_mcp_authority_operations_mode_schema_is_catalog_backed() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    catalog = importlib.import_module("med_autoscience.authority_operation_command_catalog")
    tools = {tool["name"]: tool for tool in module.build_tool_manifest()}
    mode_schema = tools["authority_operations"]["inputSchema"]["properties"]["mode"]

    assert mode_schema == catalog.build_authority_product_entry_mode_schema()


def test_mcp_authority_operations_schema_exposes_storage_governance_modes_from_catalog() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    catalog = importlib.import_module("med_autoscience.authority_operation_command_catalog")
    tools = {tool["name"]: tool for tool in module.build_tool_manifest()}
    mode_schema = tools["authority_operations"]["inputSchema"]["properties"]["mode"]

    expected_modes = {
        item.mcp_mode
        for item in catalog.AUTHORITY_OPERATION_COMMANDS
        if item.surface in {
            "storage_governance_report",
            "delivery_authority_backfill_apply",
        }
    }

    assert expected_modes == {
        "storage_governance_report",
        "delivery_authority_backfill_apply",
    }
    assert expected_modes.issubset(set(mode_schema["enum"]))
    assert "cleanup_apply" not in mode_schema["enum"]
    assert "safe_cache_cleanup_apply" not in mode_schema["enum"]


def test_mcp_server_exposes_medical_reporting_audit_tool() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    tools = module.build_tool_manifest()
    descriptions = {tool["name"]: tool["description"] for tool in tools}
    assert "publication_status" in descriptions
    assert "medical_reporting_audit" in descriptions["publication_status"]
    assert "medical_literature_audit" in descriptions["publication_status"]


def test_mcp_server_does_not_resurrect_study_runtime_tool() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    tools = {tool["name"]: tool for tool in module.build_tool_manifest()}

    assert "study_runtime" not in tools
    assert "study_progress" in tools


def test_mcp_server_doctor_tool_describes_backend_audit_surface() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    descriptions = {tool["name"]: tool["description"] for tool in module.build_tool_manifest()}

    description = descriptions["doctor_audit"]

    assert "backend_audit" in description
    assert "backend_" + "upgrade" not in description
    assert "med_deepscientist_" + "upgrade" not in description


@pytest.mark.parametrize("removed_mode", ("med_deepscientist_" + "upgrade", "backend_" + "upgrade"))
def test_mcp_server_rejects_removed_backend_audit_modes(tmp_path: Path, removed_mode: str) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    result = module.call_tool("doctor_audit", {"mode": removed_mode, "profile_path": str(profile_path)})

    assert result["isError"] is True
    assert f"Unsupported doctor_audit mode: {removed_mode}" in result["content"][0]["text"]


def test_mcp_server_can_call_doctor_report_tool(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    result = module.call_tool("doctor_audit", {"mode": "report", "profile_path": str(profile_path)})

    assert result["isError"] is False
    assert result["content"]
    assert "profile: nfpitnet" in result["content"][0]["text"]
    assert "default_publication_profile: general_medical_journal" in result["content"][0]["text"]


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

    assert progress_result["isError"] is False
    assert progress_result["structuredContent"]["quest_root"] == str(workspace_root / "runtime" / "quests" / "quest-001")
    assert progress_result["structuredContent"]["authority_snapshot"]["canonical_runtime_action"]


def test_mcp_workspace_readiness_rejects_removed_cockpit_mode(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    result = module.call_tool(
        "workspace_readiness",
        {
            "mode": "cockpit",
            "profile_path": str(profile_path),
        },
    )

    assert result["isError"] is True
    assert "Unsupported workspace_readiness mode: cockpit" in result["content"][0]["text"]


def test_mcp_server_rejects_study_runtime_tool_calls(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    result = module.call_tool(
        "study_runtime",
        {
            "mode": "request_opl_stage_attempt",
            "profile_path": str(profile_path),
            "study_id": "001-risk",
            "entry_mode": "full_research",
            "allow_stopped_relaunch": True,
            "force": True,
        },
    )

    assert result["isError"] is True
    assert result["content"][0]["text"] == "Unknown tool: study_runtime"


def test_mcp_server_rejects_ensure_study_runtime_mode_on_retired_mcp_tool(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    result = module.call_tool(
        "study_runtime",
        {
            "mode": "request_opl_stage_attempt",
            "profile_path": str(profile_path),
            "study_id": "001-risk",
        },
    )

    assert result["isError"] is True
    assert result["content"][0]["text"] == "Unknown tool: study_runtime"


def test_mcp_server_progress_projection_prefers_progress_projection_markdown_when_available(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    monkeypatch.setattr(
        module.study_progress,
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
    projection = result["structuredContent"]
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

    monkeypatch.setattr(module.study_progress, "read_study_progress", fake_read_study_progress)
    monkeypatch.setattr(
        module.study_progress,
        "render_study_progress_markdown",
        lambda payload: "# 研究进度\n\n托管运行时正在自动推进研究。\n",
    )

    result = module.call_tool(
        "study_progress",
        {
            "profile_path": str(profile_path),
            "study_id": "001-risk",
        },
    )

    assert result["isError"] is False
    assert captured["sync_runtime_summary"] is False
    assert result["structuredContent"]["study_id"] == "001-risk"
    assert result["structuredContent"]["current_stage"] == "live"
    assert result["structuredContent"]["state_label"] == "自动运行中"
    assert result["structuredContent"]["mcp_projection"]["compacted"] is True
    assert result["structuredContent"]["current_blockers"][-1] == "blocker-11"
    assert len(result["structuredContent"]["task_intake"]["constraints"]) == 8
    assert "submission_revision_operating_contract" not in result["structuredContent"]["task_intake"]
    assert "latest_evidence_packets" not in result["structuredContent"]["runtime_efficiency"]
    monitoring = result["structuredContent"]["progress_first_monitoring_summary"]
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


def test_mcp_authority_operations_can_call_workspace_authority_migration_audit(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    captured: dict[str, object] = {}

    def fake_run_migration_audit(*, workspace_roots, dry_run: bool) -> dict[str, object]:
        captured["workspace_roots"] = list(workspace_roots)
        captured["dry_run"] = dry_run
        return {
            "surface": "workspace_authority_migration_audit",
            "report_id": "workspace-authority-migration-audit::mock",
            "recorded_at": "1970-01-01T00:00:00+00:00",
            "workspace_fingerprint": "workspace-migration-audit::mock",
            "study_fingerprint": "study-migration-audit::mock",
            "dry_run": dry_run,
            "workspace_count": 2,
            "study_count": 4,
            "unclassified_authority_surface": 0,
            "delivery_projection_completion_plan_count": 1,
            "action_counts": {"apply": 0, "delete": 0, "write": 0, "mutating": 0},
            "mutating_actions": [],
            "studies": [
                {
                    "study_id": "001-risk",
                    "study_fingerprint": "study-migration-audit::001",
                    "workspace_fingerprint": "workspace-migration-audit::001",
                    "recorded_at": "1970-01-01T00:00:00+00:00",
                    "authority_classification": "controller_authorized",
                    "lifecycle_classification": "package_and_submission_ready",
                    "delivery_projection_completeness_reason": "current_package_and_submission_minimal_present",
                    "delivery_projection_completion_plan": None,
                }
            ],
        }

    monkeypatch.setattr(module.workspace_authority_migration_audit, "run_migration_audit", fake_run_migration_audit)

    result = module.call_tool(
        "authority_operations",
        {
            "mode": "workspace_authority_migration_audit",
            "workspace_roots": [
                str(tmp_path / "DM-CVD-Mortality-Risk"),
                str(tmp_path / "NF-PitNET"),
            ],
        },
    )

    assert result["isError"] is False
    assert captured == {
        "workspace_roots": [
            tmp_path / "DM-CVD-Mortality-Risk",
            tmp_path / "NF-PitNET",
        ],
        "dry_run": True,
    }
    assert result["structuredContent"]["dry_run"] is True
    assert result["structuredContent"]["report_id"] == "workspace-authority-migration-audit::mock"
    assert result["structuredContent"]["workspace_fingerprint"] == "workspace-migration-audit::mock"
    assert result["structuredContent"]["study_fingerprint"] == "study-migration-audit::mock"
    assert result["structuredContent"]["delivery_projection_completion_plan_count"] == 1
    assert result["structuredContent"]["action_counts"]["mutating"] == 0
    assert "workspace_authority_migration_audit" in result["content"][0]["text"]


def test_mcp_server_rejects_removed_product_entry_tool(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    result = module.call_tool(
        "product_entry",
        {
            "mode": "product_entry_manifest",
            "profile_path": str(profile_path),
        },
    )

    assert result["isError"] is True
    assert result["content"][0]["text"] == "Unknown tool: product_entry"


def test_mcp_authority_operations_rejects_cleanup_apply_mode(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")

    result = module.call_tool(
        "authority_operations",
        {
            "mode": "cleanup_apply",
            "workspace_roots": [str(tmp_path / "workspace")],
        },
    )

    assert result["isError"] is True
    assert "Unsupported authority_operations mode: cleanup_apply" in result["content"][0]["text"]


def test_mcp_authority_operations_can_call_delivery_authority_backfill_apply(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    captured: dict[str, object] = {}

    def fake_run_backfill_apply(*, workspace_roots, apply: bool, authority_snapshot=None) -> dict[str, object]:
        captured["workspace_roots"] = list(workspace_roots)
        captured["apply"] = apply
        captured["authority_snapshot"] = authority_snapshot
        return {
            "surface": "delivery_authority_backfill_apply",
            "apply": apply,
            "status": "planned",
            "workspace_count": 1,
            "action_counts": {"planned": 1, "blocked": 0, "applied": 0, "mutating": 0},
            "apply_plan": [{"actions": ["backfill_delivery_manifest_lifecycle_hook"]}],
            "applied_actions": [],
        }

    monkeypatch.setattr(module.delivery_authority_backfill_apply, "run_backfill_apply", fake_run_backfill_apply)

    result = module.call_tool(
        "authority_operations",
        {
            "mode": "delivery_authority_backfill_apply",
            "workspace_roots": [str(tmp_path / "workspace")],
            "apply": False,
            "authority_snapshot": {"surface": "authority_snapshot"},
        },
    )

    assert result["isError"] is False
    assert captured == {
        "workspace_roots": [tmp_path / "workspace"],
        "apply": False,
        "authority_snapshot": {"surface": "authority_snapshot"},
    }
    assert result["structuredContent"]["surface"] == "delivery_authority_backfill_apply"
    assert result["structuredContent"]["action_counts"]["mutating"] == 0
    assert "delivery_authority_backfill_apply" in result["content"][0]["text"]


def test_mcp_authority_operations_can_call_lifecycle_report_with_scan_options(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    captured: dict[str, object] = {}

    def fake_run_lifecycle_operations_report(*, workspace_roots, deep: bool, max_files: int, max_seconds: float) -> dict[str, object]:
        captured["workspace_roots"] = list(workspace_roots)
        captured["deep"] = deep
        captured["max_files"] = max_files
        captured["max_seconds"] = max_seconds
        return {
            "surface": "artifact_lifecycle_report",
            "workspace_count": 1,
            "scan_policy": {
                "deep_scan_enabled": deep,
                "max_files": max_files,
                "max_seconds": max_seconds,
            },
            "mutation_policy": {"read_only": True, "physical_cleanup_performed": False},
            "summary": {"total_bytes": 0},
            "projection_completeness": {"complete_study_count": 0, "incomplete_study_count": 0},
            "source_totals": {},
            "workspaces": [],
        }

    monkeypatch.setattr(
        module.artifact_lifecycle_operations_report,
        "run_lifecycle_operations_report",
        fake_run_lifecycle_operations_report,
    )

    result = module.call_tool(
        "authority_operations",
        {
            "mode": "artifact_lifecycle_report",
            "workspace_roots": [str(tmp_path / "workspace")],
            "deep": True,
            "max_files": 9,
            "max_seconds": 2.5,
        },
    )

    assert result["isError"] is False
    assert captured == {
        "workspace_roots": [tmp_path / "workspace"],
        "deep": True,
        "max_files": 9,
        "max_seconds": 2.5,
    }
    assert result["structuredContent"]["surface"] == "artifact_lifecycle_report"
    assert result["structuredContent"]["scan_policy"]["max_files"] == 9
    assert result["structuredContent"]["mutation_policy"]["physical_cleanup_performed"] is False
    assert "artifact_lifecycle_report" in result["content"][0]["text"]


def test_mcp_authority_operations_lifecycle_report_bounds_receipt_ref_families(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    retention_module = importlib.import_module("med_autoscience.controllers.artifact_retention_operations_plan")
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    for index in range(60):
        source_path = study_root / "paper" / "source" / f"manuscript-{index}.md"
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_text("source\n", encoding="utf-8")
        projection_path = study_root / "manuscript" / "current_package" / f"projection-{index}.pdf"
        projection_path.parent.mkdir(parents=True, exist_ok=True)
        projection_path.write_text("pdf\n", encoding="utf-8")

    result = module.call_tool(
        "authority_operations",
        {
            "mode": "artifact_lifecycle_report",
            "workspace_roots": [str(workspace_root)],
            "deep": True,
        },
    )

    assert result["isError"] is False
    plan = result["structuredContent"]["retention_plan"]
    assert plan["summary"]["operation_count"] == 120
    assert len(plan["artifact_lifecycle_receipt_refs"]) == retention_module.RECEIPT_REF_SAMPLE_LIMIT
    assert plan["artifact_lifecycle_receipt_ref_count"] == 120
    assert plan["artifact_lifecycle_receipt_refs_truncated"] is True
    assert len(plan["artifact_authority_receipt_refs"]) == retention_module.RECEIPT_REF_SAMPLE_LIMIT
    assert plan["artifact_authority_receipt_ref_count"] == 120
    assert plan["artifact_authority_receipt_refs_truncated"] is True
    assert len(plan["retention_receipt_refs"]) == retention_module.RECEIPT_REF_SAMPLE_LIMIT
    assert plan["retention_receipt_ref_count"] == 60
    assert plan["retention_receipt_refs_truncated"] is True
    assert plan["cleanup_receipt_ref_count"] == 0
    assert plan["restore_proof_ref_count"] == 0
    assert result["structuredContent"]["mutation_policy"]["physical_cleanup_performed"] is False


def test_mcp_server_can_call_portfolio_memory_status_tool(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    captured: dict[str, object] = {}

    def fake_status(*, workspace_root: Path) -> dict[str, object]:
        captured["workspace_root"] = workspace_root
        return {"portfolio_memory_exists": True, "asset_count": 3}

    monkeypatch.setattr(module.portfolio_memory, "portfolio_memory_status", fake_status)

    result = module.call_tool(
        "workspace_readiness",
        {
            "mode": "portfolio_memory_status",
            "workspace_root": "/tmp/medautosci-demo",
        },
    )

    assert result["isError"] is False
    assert captured["workspace_root"] == Path("/tmp/medautosci-demo")
    assert result["structuredContent"]["asset_count"] == 3


def test_mcp_server_can_call_workspace_literature_status_tool(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    captured: dict[str, object] = {}

    def fake_status(*, workspace_root: Path) -> dict[str, object]:
        captured["workspace_root"] = workspace_root
        return {"workspace_literature_exists": True, "record_count": 7}

    monkeypatch.setattr(module.workspace_literature, "workspace_literature_status", fake_status)

    result = module.call_tool(
        "workspace_readiness",
        {
            "mode": "workspace_literature_status",
            "workspace_root": "/tmp/medautosci-demo",
        },
    )

    assert result["isError"] is False
    assert captured["workspace_root"] == Path("/tmp/medautosci-demo")
    assert result["structuredContent"]["record_count"] == 7


def test_mcp_server_can_call_prepare_external_research_tool(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    captured: dict[str, object] = {}

    def fake_prepare(*, workspace_root: Path, as_of_date: str | None) -> dict[str, object]:
        captured["workspace_root"] = workspace_root
        captured["as_of_date"] = as_of_date
        return {"status": "ready", "prompt_path": "/tmp/medautosci-demo/memory/portfolio/research_memory/prompts/x.md"}

    monkeypatch.setattr(module.external_research, "prepare_external_research", fake_prepare)

    result = module.call_tool(
        "research_assets",
        {
            "mode": "prepare_external_research",
            "workspace_root": "/tmp/medautosci-demo",
            "as_of_date": "2026-03-30",
        },
    )

    assert result["isError"] is False
    assert captured["workspace_root"] == Path("/tmp/medautosci-demo")
    assert captured["as_of_date"] == "2026-03-30"
    assert result["structuredContent"]["status"] == "ready"


def test_mcp_server_can_call_init_workspace_tool(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    captured: dict[str, object] = {}

    def fake_init_workspace(
        *,
        workspace_root: Path,
        workspace_name: str,
        default_publication_profile: str,
        default_citation_style: str,
        dry_run: bool,
        force: bool,
        initialize_git: bool,
    ) -> dict[str, object]:
        captured["workspace_root"] = workspace_root
        captured["workspace_name"] = workspace_name
        captured["default_publication_profile"] = default_publication_profile
        captured["default_citation_style"] = default_citation_style
        captured["dry_run"] = dry_run
        captured["force"] = force
        captured["initialize_git"] = initialize_git
        return {
            "workspace_root": str(workspace_root),
            "workspace_name": workspace_name,
            "profile_path": str(workspace_root / "ops" / "medautoscience" / "profiles" / "demo.local.toml"),
            "dry_run": dry_run,
            "force": force,
            "workspace_git": {"enabled": initialize_git},
            "created_directories": [],
            "written_files": [],
        }

    monkeypatch.setattr(module.workspace_init, "init_workspace", fake_init_workspace)

    result = module.call_tool(
        "workspace_readiness",
        {
            "mode": "init_workspace",
            "workspace_root": "/tmp/medautosci-demo",
            "workspace_name": "NF-PitNET Demo",
            "default_publication_profile": "oncology_medical_journal",
            "default_citation_style": "Vancouver",
            "dry_run": True,
            "force": True,
        },
    )

    assert result["isError"] is False
    assert captured == {
        "workspace_root": Path("/tmp/medautosci-demo"),
        "workspace_name": "NF-PitNET Demo",
        "default_publication_profile": "oncology_medical_journal",
        "default_citation_style": "Vancouver",
        "dry_run": True,
        "force": True,
        "initialize_git": False,
    }
    assert result["structuredContent"]["workspace_name"] == "NF-PitNET Demo"
    assert '"workspace_name": "NF-PitNET Demo"' in result["content"][0]["text"]
