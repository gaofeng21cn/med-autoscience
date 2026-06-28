from __future__ import annotations

import importlib
from pathlib import Path

from tests.mcp_server_cases.result_envelope import _structured_payload

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
    assert _structured_payload(result)["asset_count"] == 3
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
    assert _structured_payload(result)["record_count"] == 7
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
    assert result["structuredContent"]["status"] == "succeeded"
    assert _structured_payload(result)["status"] == "ready"
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
    assert _structured_payload(result)["workspace_name"] == "NF-PitNET Demo"
    assert '"workspace_name": "NF-PitNET Demo"' in result["content"][0]["text"]
