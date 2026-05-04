from __future__ import annotations

import importlib
from pathlib import Path

import pytest


def write_profile(path: Path) -> None:
    path.write_text(
        "\n".join(
            [
                'name = "nfpitnet"',
                'workspace_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤"',
                'runtime_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/med-deepscientist/runtime/quests"',
                'studies_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/studies"',
                'portfolio_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/portfolio"',
                'med_deepscientist_runtime_root = "/Users/gaofeng/workspace/Yang/无功能垂体瘤/ops/med-deepscientist/runtime"',
                'med_deepscientist_repo_root = "/Users/gaofeng/workspace/med-deepscientist"',
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
        "publication_status",
        "product_entry",
    ]


@pytest.mark.parametrize(
    "fragment",
    ("migration_audit", "cleanup_apply", "lifecycle_report", "dry-run", "contract-gated"),
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


def test_mcp_server_doctor_tool_describes_backend_upgrade_surface() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    descriptions = {tool["name"]: tool["description"] for tool in module.build_tool_manifest()}

    description = descriptions["doctor_audit"]

    assert "backend_upgrade" in description
    assert "med_deepscientist_upgrade" not in description


def test_mcp_server_can_call_doctor_report_tool(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    result = module.call_tool("doctor_audit", {"mode": "report", "profile_path": str(profile_path)})

    assert result["isError"] is False
    assert result["content"]
    assert "profile: nfpitnet" in result["content"][0]["text"]
    assert "default_publication_profile: general_medical_journal" in result["content"][0]["text"]


def test_mcp_server_can_call_ensure_study_runtime_tool(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_id, study_root, entry_mode, allow_stopped_relaunch, force, source: {
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


def test_mcp_compacts_and_renders_open_auto_research_projection() -> None:
    module = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    payload = {
        "schema_version": 1,
        "study_id": "001-risk",
        "current_stage": "publication_supervision",
        "paper_stage": "write",
        "open_auto_research_projection": {
            "surface": "open_auto_research_projection",
            "status": "needs_review",
            "summary": "3 ready, 1 needs review.",
            "counts": {"ready": 3, "blocked": 0, "needs_review": 1, "total": 4},
            "actions": [
                {
                    "action_id": "review_rubric_gaps",
                    "status": "needs_review",
                    "surface": "paperbench_style_hierarchical_rubric_tree",
                }
            ],
            "authority": {"read_only": True, "can_authorize_publication_quality": False},
        },
    }

    compact = module.compact_study_progress_projection(payload)
    markdown = module.render_mcp_study_progress_markdown(payload)

    projection = compact["open_auto_research_projection"]
    assert projection["status"] == "needs_review"
    assert projection["counts"]["needs_review"] == 1
    assert projection["actions"][0]["action_id"] == "review_rubric_gaps"
    assert projection["authority"]["read_only"] is True
    assert "Open Auto Research" in markdown
    assert "review_rubric_gaps" in markdown


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
    assert result["structuredContent"]["current_stage"] == "managed_runtime_active"
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


def test_mcp_product_entry_can_call_cleanup_apply(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    captured: dict[str, object] = {}

    def fake_run_cleanup_apply(*, workspace_roots, apply: bool, control_plane_snapshot=None) -> dict[str, object]:
        captured["workspace_roots"] = list(workspace_roots)
        captured["apply"] = apply
        captured["control_plane_snapshot"] = control_plane_snapshot
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
    }
    assert result["structuredContent"]["surface"] == "control_plane_cleanup_apply"
    assert result["structuredContent"]["action_counts"]["mutating"] == 0
    assert "control_plane_cleanup_apply" in result["content"][0]["text"]


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
            "initialize_git": False,
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
