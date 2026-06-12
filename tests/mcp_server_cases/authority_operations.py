from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from tests.mcp_server_cases.result_envelope import _structured_payload


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
    payload = _structured_payload(result)
    assert payload["dry_run"] is True
    assert payload["report_id"] == "workspace-authority-migration-audit::mock"
    assert payload["workspace_fingerprint"] == "workspace-migration-audit::mock"
    assert payload["study_fingerprint"] == "study-migration-audit::mock"
    assert payload["delivery_projection_completion_plan_count"] == 1
    assert payload["action_counts"]["mutating"] == 0
    assert "workspace_authority_migration_audit" in result["content"][0]["text"]


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
    payload = _structured_payload(result)
    assert payload["surface"] == "delivery_authority_backfill_apply"
    assert payload["action_counts"]["mutating"] == 0
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
    payload = _structured_payload(result)
    assert payload["surface"] == "artifact_lifecycle_report"
    assert payload["scan_policy"]["max_files"] == 9
    assert payload["mutation_policy"]["physical_cleanup_performed"] is False
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
    payload = _structured_payload(result)
    plan = payload["retention_plan"]
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
    assert payload["mutation_policy"]["physical_cleanup_performed"] is False
