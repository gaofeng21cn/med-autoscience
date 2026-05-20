from __future__ import annotations

import builtins
import importlib
import sys
from pathlib import Path

import pytest

from tests.mcp_server_cases.delivery_inspection_visibility import *
from tests.mcp_server_cases.open_auto_research_projection import *


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

    assert [tool["name"] for tool in module.list_tools()] == [
        "doctor_audit",
        "workspace_readiness",
        "research_assets",
        "study_runtime",
        "study_progress",
        "open_auto_research_soak",
        "publication_status",
        "product_entry",
    ]


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

    assert names == [
        "doctor_audit",
        "workspace_readiness",
        "research_assets",
        "study_runtime",
        "study_progress",
        "open_auto_research_soak",
        "publication_status",
        "product_entry",
    ]


@pytest.mark.parametrize(
    "fragment",
    (
        "migration_audit",
        "governance_report",
        "backfill_apply",
        "safe_cache_cleanup_apply",
        "cleanup_apply",
        "lifecycle_report",
        "dry-run",
        "contract-gated",
        "delete-safe-cache",
    ),
)
def test_mcp_product_entry_description_documents_control_plane_operations_surfaces(fragment: str) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    tools = {tool["name"]: tool for tool in module.build_tool_manifest()}

    assert fragment in tools["product_entry"]["description"]


@pytest.mark.parametrize(
    ("option", "schema"),
    (
        ("apply", {"type": "boolean"}),
        ("markdown", {"type": "boolean"}),
        ("deep", {"type": "boolean"}),
        ("max_files", {"type": "integer", "minimum": 1}),
        ("max_seconds", {"type": "number", "exclusiveMinimum": 0}),
        ("control_plane_snapshot", {"type": "object"}),
    ),
)
def test_mcp_product_entry_schema_accepts_control_plane_operations_options(
    option: str,
    schema: dict[str, object],
) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    tools = {tool["name"]: tool for tool in module.build_tool_manifest()}
    properties = tools["product_entry"]["inputSchema"]["properties"]

    assert properties[option] == schema


def test_mcp_product_entry_mode_schema_is_catalog_backed() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    catalog = importlib.import_module("med_autoscience.control_plane_command_catalog")
    tools = {tool["name"]: tool for tool in module.build_tool_manifest()}
    mode_schema = tools["product_entry"]["inputSchema"]["properties"]["mode"]

    assert mode_schema == catalog.build_control_plane_product_entry_mode_schema()


def test_mcp_product_entry_schema_exposes_storage_governance_modes_from_catalog() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    catalog = importlib.import_module("med_autoscience.control_plane_command_catalog")
    tools = {tool["name"]: tool for tool in module.build_tool_manifest()}
    mode_schema = tools["product_entry"]["inputSchema"]["properties"]["mode"]

    expected_modes = {
        item.mcp_mode
        for item in catalog.CONTROL_PLANE_OPERATIONS_COMMANDS
        if item.surface in {
            "storage_governance_report",
            "control_plane_backfill_apply",
            "control_plane_safe_cache_cleanup_apply",
        }
    }

    assert expected_modes == {
        "governance_report",
        "backfill_apply",
        "safe_cache_cleanup_apply",
    }
    assert expected_modes.issubset(set(mode_schema["enum"]))


def test_mcp_server_exposes_medical_reporting_audit_tool() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    tools = module.build_tool_manifest()
    descriptions = {tool["name"]: tool["description"] for tool in tools}
    assert "publication_status" in descriptions
    assert "medical_reporting_audit" in descriptions["publication_status"]
    assert "medical_literature_audit" in descriptions["publication_status"]


def test_mcp_server_documents_live_runtime_guard_on_study_runtime_tools() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    descriptions = {tool["name"]: tool["description"] for tool in module.build_tool_manifest()}

    description = descriptions["study_runtime"]

    assert "autonomous_runtime_notice.required = true" in description
    assert "execution_owner_guard.supervisor_only = true" in description
    assert "notify the user" in description
    assert "supervisor-only" in description
    assert "bundle_tasks_downstream_only = true" in description
    assert "bundle/build/proofing" in description


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


def test_mcp_default_status_progress_and_cockpit_do_not_require_external_mds_repo(tmp_path: Path) -> None:
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
                "  runtime_backend_id: mas_runtime_core",
                "  runtime_backend: mas_runtime_core",
                "  runtime_engine_id: mas-runtime-core",
                "  research_backend_id: mas_runtime_core",
                "  research_backend: mas_runtime_core",
                "  research_engine_id: mas-runtime-core",
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
                f'portfolio_root = "{workspace_root / "portfolio"}"',
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

    status_result = module.call_tool(
        "study_runtime",
        {
            "mode": "study_runtime_status",
            "profile_path": str(profile_path),
            "study_id": "001-risk",
        },
    )
    progress_result = module.call_tool(
        "study_progress",
        {
            "profile_path": str(profile_path),
            "study_id": "001-risk",
        },
    )
    cockpit_result = module.call_tool(
        "workspace_readiness",
        {
            "mode": "cockpit",
            "profile_path": str(profile_path),
        },
    )

    assert status_result["isError"] is False
    assert progress_result["isError"] is False
    assert cockpit_result["isError"] is False
    assert status_result["structuredContent"]["execution"]["runtime_backend_id"] == "mas_runtime_core"
    assert progress_result["structuredContent"]["quest_root"] == str(workspace_root / "runtime" / "quests" / "quest-001")
    assert cockpit_result["structuredContent"]["profile_name"] == "minimal"


def test_mcp_server_can_call_ensure_study_runtime_tool(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_id, study_root, entry_mode, allow_stopped_relaunch, force, source, explicit_user_wakeup: {
            "decision": "create_and_start",
            "study_id": study_id,
            "quest_id": study_id,
            "allow_stopped_relaunch": allow_stopped_relaunch,
            "source": source,
        },
    )

    result = module.call_tool(
        "study_runtime",
        {
            "mode": "ensure_study_runtime",
            "profile_path": str(profile_path),
            "study_id": "001-risk",
            "entry_mode": "full_research",
            "allow_stopped_relaunch": True,
            "force": True,
        },
    )

    assert result["isError"] is False
    assert result["structuredContent"]["decision"] == "create_and_start"
    assert result["structuredContent"]["quest_id"] == "001-risk"
    assert result["structuredContent"]["allow_stopped_relaunch"] is True


def test_mcp_server_can_serialize_typed_ensure_study_runtime_result(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **kwargs: typed_surface.StudyRuntimeStatus.from_payload(
            {
                "schema_version": 1,
                "study_id": "001-risk",
                "study_root": "/tmp/studies/001-risk",
                "entry_mode": "full_research",
                "execution": {"quest_id": "001-risk", "auto_resume": True},
                "quest_id": "001-risk",
                "quest_root": "/tmp/runtime/quests/001-risk",
                "quest_exists": True,
                "quest_status": "created",
                "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
                "runtime_binding_exists": True,
                "study_completion_contract": {},
                "decision": "create_and_start",
                "reason": "quest_missing",
            }
        ),
    )

    result = module.call_tool(
        "study_runtime",
        {
            "mode": "ensure_study_runtime",
            "profile_path": str(profile_path),
            "study_id": "001-risk",
        },
    )

    assert result["isError"] is False
    assert result["structuredContent"]["decision"] == "create_and_start"
    assert result["structuredContent"]["study_id"] == "001-risk"


def test_mcp_server_can_serialize_typed_study_runtime_status_result(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    typed_surface = importlib.import_module("med_autoscience.controllers.study_runtime_types")

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **kwargs: typed_surface.StudyRuntimeStatus.from_payload(
            {
                "schema_version": 1,
                "study_id": "001-risk",
                "study_root": "/tmp/studies/001-risk",
                "entry_mode": "full_research",
                "execution": {"quest_id": "001-risk", "auto_resume": True},
                "quest_id": "001-risk",
                "quest_root": "/tmp/runtime/quests/001-risk",
                "quest_exists": True,
                "quest_status": "created",
                "runtime_binding_path": "/tmp/studies/001-risk/runtime_binding.yaml",
                "runtime_binding_exists": True,
                "study_completion_contract": {},
                "decision": "noop",
                "reason": "quest_missing",
            }
        ),
    )

    result = module.call_tool(
        "study_runtime",
        {
            "mode": "study_runtime_status",
            "profile_path": str(profile_path),
            "study_id": "001-risk",
        },
    )

    assert result["isError"] is False
    assert result["structuredContent"]["decision"] == "noop"
    assert result["structuredContent"]["study_id"] == "001-risk"


def test_mcp_server_study_runtime_status_prefers_progress_projection_markdown_when_available(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **kwargs: {
            "schema_version": 1,
            "study_id": "001-risk",
            "decision": "noop",
            "quest_status": "running",
            "progress_projection": {
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
        },
    )

    result = module.call_tool(
        "study_runtime",
        {
            "mode": "study_runtime_status",
            "profile_path": str(profile_path),
            "study_id": "001-risk",
        },
    )

    assert result["isError"] is False
    projection = result["structuredContent"]["progress_projection"]
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
    assert "自动推进研究" in result["content"][0]["text"]


def test_mcp_product_entry_can_call_migration_audit(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    captured: dict[str, object] = {}

    def fake_run_migration_audit(*, workspace_roots, dry_run: bool) -> dict[str, object]:
        captured["workspace_roots"] = list(workspace_roots)
        captured["dry_run"] = dry_run
        return {
            "surface": "control_plane_migration_audit",
            "report_id": "control-plane-migration-audit::mock",
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

    monkeypatch.setattr(module.control_plane_migration_audit, "run_migration_audit", fake_run_migration_audit)

    result = module.call_tool(
        "product_entry",
        {
            "mode": "migration_audit",
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
    assert result["structuredContent"]["report_id"] == "control-plane-migration-audit::mock"
    assert result["structuredContent"]["workspace_fingerprint"] == "workspace-migration-audit::mock"
    assert result["structuredContent"]["study_fingerprint"] == "study-migration-audit::mock"
    assert result["structuredContent"]["delivery_projection_completion_plan_count"] == 1
    assert result["structuredContent"]["action_counts"]["mutating"] == 0
    assert "control_plane_migration_audit" in result["content"][0]["text"]


def test_mcp_product_entry_manifest_exposes_generated_caller_retirement_proof(tmp_path: Path) -> None:
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

    assert result["isError"] is False
    manifest = result["structuredContent"]
    boundary = manifest["functional_consumer_boundary"]
    generated_default = boundary["generated_default_caller_boundary"]
    assert generated_default["status"] == "opl_generated_hosted_shell_is_default_caller"
    assert generated_default["default_caller_owner"] == "one-person-lab"
    assert generated_default["all_default_callers_migrated"] is True
    mcp_surface = {
        item["surface_id"]: item for item in generated_default["surface_boundaries"]
    }["mcp"]
    assert mcp_surface["mas_retained_role"] == "domain_handler_target"
    assert mcp_surface["parity_ref"] == "mcp_descriptor_parity"
    assert mcp_surface["mas_generic_owner_allowed"] is False
    retirement_matrix = boundary["physical_retirement_gate_matrix"]
    candidates = {item["surface_id"]: item for item in retirement_matrix["retirement_candidates"]}
    assert candidates["sidecar_adapter"]["active_default_caller_count"] == 0
    assert candidates["sidecar_adapter"]["physical_delete_permitted"] is False
    assert candidates["status_projection"]["retained_as"] == "domain_truth_status_projection"
    assert manifest["runtime_transport_handoff_projection"]["generated_default_caller_boundary"] == (
        generated_default
    )


def test_mcp_product_entry_can_call_cleanup_apply(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    captured: dict[str, object] = {}

    def fake_run_cleanup_apply(
        *,
        workspace_roots,
        apply: bool,
        control_plane_snapshot=None,
        retention_report=None,
    ) -> dict[str, object]:
        captured["workspace_roots"] = list(workspace_roots)
        captured["apply"] = apply
        captured["control_plane_snapshot"] = control_plane_snapshot
        captured["retention_report"] = retention_report
        return {
            "surface": "control_plane_cleanup_apply",
            "apply": apply,
            "status": "planned",
            "workspace_count": 1,
            "action_counts": {"planned": 1, "blocked": 0, "applied": 0, "mutating": 0},
            "apply_plan": [{"action": "delete-safe-cache"}],
            "applied_actions": [],
        }

    monkeypatch.setattr(module.control_plane_cleanup_apply, "run_cleanup_apply", fake_run_cleanup_apply)

    result = module.call_tool(
        "product_entry",
        {
            "mode": "cleanup_apply",
            "workspace_roots": [str(tmp_path / "workspace")],
            "apply": False,
            "control_plane_snapshot": {"surface": "control_plane_snapshot"},
        },
    )

    assert result["isError"] is False
    assert captured == {
        "workspace_roots": [tmp_path / "workspace"],
        "apply": False,
        "control_plane_snapshot": {"surface": "control_plane_snapshot"},
        "retention_report": None,
    }
    assert result["structuredContent"]["surface"] == "control_plane_cleanup_apply"
    assert result["structuredContent"]["action_counts"]["mutating"] == 0
    assert "control_plane_cleanup_apply" in result["content"][0]["text"]


def test_mcp_product_entry_can_call_backfill_apply(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    captured: dict[str, object] = {}

    def fake_run_backfill_apply(*, workspace_roots, apply: bool, control_plane_snapshot=None) -> dict[str, object]:
        captured["workspace_roots"] = list(workspace_roots)
        captured["apply"] = apply
        captured["control_plane_snapshot"] = control_plane_snapshot
        return {
            "surface": "control_plane_backfill_apply",
            "apply": apply,
            "status": "planned",
            "workspace_count": 1,
            "action_counts": {"planned": 1, "blocked": 0, "applied": 0, "mutating": 0},
            "apply_plan": [{"actions": ["backfill_delivery_manifest_lifecycle_hook"]}],
            "applied_actions": [],
        }

    monkeypatch.setattr(module.control_plane_backfill_apply, "run_backfill_apply", fake_run_backfill_apply)

    result = module.call_tool(
        "product_entry",
        {
            "mode": "backfill_apply",
            "workspace_roots": [str(tmp_path / "workspace")],
            "apply": False,
            "control_plane_snapshot": {"surface": "control_plane_snapshot"},
        },
    )

    assert result["isError"] is False
    assert captured == {
        "workspace_roots": [tmp_path / "workspace"],
        "apply": False,
        "control_plane_snapshot": {"surface": "control_plane_snapshot"},
    }
    assert result["structuredContent"]["surface"] == "control_plane_backfill_apply"
    assert result["structuredContent"]["action_counts"]["mutating"] == 0
    assert "control_plane_backfill_apply" in result["content"][0]["text"]


def test_mcp_product_entry_can_call_lifecycle_report_with_scan_options(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    captured: dict[str, object] = {}

    def fake_run_lifecycle_operations_report(*, workspace_roots, deep: bool, max_files: int, max_seconds: float) -> dict[str, object]:
        captured["workspace_roots"] = list(workspace_roots)
        captured["deep"] = deep
        captured["max_files"] = max_files
        captured["max_seconds"] = max_seconds
        return {
            "surface": "control_plane_lifecycle_report",
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
        "product_entry",
        {
            "mode": "lifecycle_report",
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
    assert result["structuredContent"]["surface"] == "control_plane_lifecycle_report"
    assert result["structuredContent"]["scan_policy"]["max_files"] == 9
    assert result["structuredContent"]["mutation_policy"]["physical_cleanup_performed"] is False
    assert "control_plane_lifecycle_report" in result["content"][0]["text"]


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
        return {"status": "ready", "prompt_path": "/tmp/medautosci-demo/portfolio/research_memory/prompts/x.md"}

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
