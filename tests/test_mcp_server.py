from __future__ import annotations

import importlib
from pathlib import Path


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
        "doctor_report",
        "show_profile",
        "overlay_status",
        "runtime_watch",
        "data_assets_status",
        "portfolio_memory_status",
        "init_portfolio_memory",
        "external_research_status",
        "prepare_external_research",
        "startup_data_readiness",
        "med_deepscientist_upgrade_check",
        "study_runtime_status",
        "study_progress",
        "ensure_study_runtime",
        "init_workspace",
        "medical_literature_audit",
        "medical_reporting_audit",
    ]


def test_mcp_server_exposes_medical_reporting_audit_tool() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    tools = module.build_tool_manifest()
    tool_names = {tool["name"] for tool in tools}
    assert "medical_reporting_audit" in tool_names
    assert "medical_literature_audit" in tool_names


def test_mcp_server_documents_live_runtime_guard_on_study_runtime_tools() -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    descriptions = {tool["name"]: tool["description"] for tool in module.build_tool_manifest()}

    status_description = descriptions["study_runtime_status"]
    ensure_description = descriptions["ensure_study_runtime"]

    for description in (status_description, ensure_description):
        assert "autonomous_runtime_notice.required = true" in description
        assert "execution_owner_guard.supervisor_only = true" in description
        assert "notify the user" in description
        assert "supervisor-only" in description
        assert "bundle_tasks_downstream_only = true" in description
        assert "bundle/build/proofing" in description


def test_mcp_server_can_call_doctor_report_tool(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    result = module.call_tool("doctor_report", {"profile_path": str(profile_path)})

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
        "ensure_study_runtime",
        {
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
        "ensure_study_runtime",
        {
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
        "study_runtime_status",
        {
            "profile_path": str(profile_path),
            "study_id": "001-risk",
        },
    )

    assert result["isError"] is False
    assert result["structuredContent"]["decision"] == "noop"
    assert result["structuredContent"]["study_id"] == "001-risk"


def test_mcp_server_can_call_study_progress_tool(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)

    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": "001-risk",
            "current_stage": "managed_runtime_active",
            "current_stage_summary": "托管运行时正在自动推进研究。",
        },
    )
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
    assert result["structuredContent"]["study_id"] == "001-risk"
    assert result["structuredContent"]["current_stage"] == "managed_runtime_active"
    assert "自动推进研究" in result["content"][0]["text"]


def test_mcp_server_can_call_portfolio_memory_status_tool(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    captured: dict[str, object] = {}

    def fake_status(*, workspace_root: Path) -> dict[str, object]:
        captured["workspace_root"] = workspace_root
        return {"portfolio_memory_exists": True, "asset_count": 3}

    monkeypatch.setattr(module.portfolio_memory, "portfolio_memory_status", fake_status)

    result = module.call_tool(
        "portfolio_memory_status",
        {
            "workspace_root": "/tmp/medautosci-demo",
        },
    )

    assert result["isError"] is False
    assert captured["workspace_root"] == Path("/tmp/medautosci-demo")
    assert result["structuredContent"]["asset_count"] == 3


def test_mcp_server_can_call_prepare_external_research_tool(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.mcp_server")
    captured: dict[str, object] = {}

    def fake_prepare(*, workspace_root: Path, as_of_date: str | None) -> dict[str, object]:
        captured["workspace_root"] = workspace_root
        captured["as_of_date"] = as_of_date
        return {"status": "ready", "prompt_path": "/tmp/medautosci-demo/portfolio/research_memory/prompts/x.md"}

    monkeypatch.setattr(module.external_research, "prepare_external_research", fake_prepare)

    result = module.call_tool(
        "prepare_external_research",
        {
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
    ) -> dict[str, object]:
        captured["workspace_root"] = workspace_root
        captured["workspace_name"] = workspace_name
        captured["default_publication_profile"] = default_publication_profile
        captured["default_citation_style"] = default_citation_style
        captured["dry_run"] = dry_run
        captured["force"] = force
        return {
            "workspace_root": str(workspace_root),
            "workspace_name": workspace_name,
            "profile_path": str(workspace_root / "ops" / "medautoscience" / "profiles" / "demo.local.toml"),
            "dry_run": dry_run,
            "force": force,
            "created_directories": [],
            "written_files": [],
        }

    monkeypatch.setattr(module.workspace_init, "init_workspace", fake_init_workspace)

    result = module.call_tool(
        "init_workspace",
        {
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
    }
    assert result["structuredContent"]["workspace_name"] == "NF-PitNET Demo"
    assert '"workspace_name": "NF-PitNET Demo"' in result["content"][0]["text"]
