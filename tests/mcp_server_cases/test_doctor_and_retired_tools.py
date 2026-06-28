from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from tests.mcp_server_cases.profile import write_profile

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
    envelope = result["structuredContent"]
    assert envelope["surface_kind"] == "mas_tool_result_envelope"
    assert envelope["tool_id"] == "workspace_readiness"
    assert envelope["status"] == "failed"
    assert envelope["error_class"] == "tool_execution_error"
    assert envelope["authority_boundary"]["tool_result_envelope_is_authority_outcome"] is False
    assert envelope["authority_boundary"]["can_write_domain_truth"] is False
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
