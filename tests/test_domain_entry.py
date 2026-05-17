from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study


def test_domain_entry_dispatches_product_entry_status(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    monkeypatch.setattr(module, "load_profile", lambda ref: profile)
    monkeypatch.setattr(
        module.product_entry,
        "build_product_entry_status",
        lambda *, profile, profile_ref=None: {
            "surface_kind": "product_entry_status",
            "target_domain_id": "med-autoscience",
        },
    )

    payload = module.MedAutoScienceDomainEntry().dispatch(
        {
            "command": "product-entry-status",
            "profile_ref": str(profile_ref),
        }
    )

    assert payload == {
        "command": "product-entry-status",
        "surface_kind": "product_entry_status",
        "target_domain_id": "med-autoscience",
    }


def test_domain_entry_dispatches_skill_catalog(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"

    monkeypatch.setattr(module, "load_profile", lambda ref: profile)
    monkeypatch.setattr(
        module.product_entry,
        "build_skill_catalog",
        lambda *, profile, profile_ref=None: {
            "surface_kind": "skill_catalog",
            "skills": [{"skill_id": "mas_workspace_cockpit"}],
        },
    )

    payload = module.MedAutoScienceDomainEntry().dispatch(
        {
            "command": "skill-catalog",
            "profile_ref": str(profile_ref),
        }
    )

    assert payload == {
        "command": "skill-catalog",
        "surface_kind": "skill_catalog",
        "skills": [{"skill_id": "mas_workspace_cockpit"}],
    }


def test_external_caller_can_consume_domain_entry_contract_without_repo_local_helper(
    monkeypatch,
    tmp_path: Path,
) -> None:
    product_entry_module = importlib.import_module("med_autoscience.controllers.product_entry")
    domain_entry_module = importlib.import_module("med_autoscience.domain_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")

    product_entry_module.submit_study_task(
        profile=profile,
        study_id="001-risk",
        task_intent="继续用统一 product entry contract 驱动 MAS，而不是暴露底层命令。",
        entry_mode="full_research",
    )

    product_entry_payload = product_entry_module.build_product_entry(
        profile=profile,
        profile_ref=profile_ref,
        study_id="001-risk",
        direct_entry_mode="opl-handoff",
    )
    contract = product_entry_payload["return_surface_contract"]["domain_entry_contract"]

    monkeypatch.setattr(domain_entry_module, "load_profile", lambda ref: profile)
    monkeypatch.setattr(
        domain_entry_module.study_progress,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": "001-risk",
            "current_stage": "publication_supervision",
            "current_stage_summary": "当前由 MAS 监管论文推进。",
        },
    )

    request = _build_request_from_contract(
        contract,
        "study-progress",
        profile_ref=str(profile_ref),
        study_id="001-risk",
    )
    payload = domain_entry_module.MedAutoScienceDomainEntry().dispatch(request)

    assert request == {
        "command": "study-progress",
        "profile_ref": str(profile_ref),
        "study_id": "001-risk",
    }
    assert payload["command"] == "study-progress"
    assert payload["current_stage"] == "publication_supervision"


def test_domain_entry_rejects_missing_required_fields(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")

    with pytest.raises(ValueError, match="缺少必填字段"):
        module.MedAutoScienceDomainEntry().dispatch(
            {
                "command": "study-progress",
                "profile_ref": str(tmp_path / "profile.local.toml"),
            }
        )


def test_domain_entry_dispatches_control_plane_operations(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")
    workspace_root = tmp_path / "workspace"

    monkeypatch.setattr(
        module.control_plane_migration_audit,
        "run_migration_audit",
        lambda *, workspace_roots, dry_run: {
            "surface": "control_plane_migration_audit",
            "workspace_roots": [str(path) for path in workspace_roots],
            "dry_run": dry_run,
        },
    )

    payload = module.MedAutoScienceDomainEntry().dispatch(
        {
            "command": "control-plane-migration-audit",
            "workspace_roots": [str(workspace_root)],
        }
    )

    assert payload == {
        "command": "control-plane-migration-audit",
        "surface": "control_plane_migration_audit",
        "workspace_roots": [str(workspace_root)],
        "dry_run": True,
    }


def test_domain_entry_dispatches_lifecycle_report_scan_options(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")
    workspace_root = tmp_path / "workspace"

    monkeypatch.setattr(
        module.artifact_lifecycle_operations_report,
        "run_lifecycle_operations_report",
        lambda *, workspace_roots, deep, max_files, max_seconds: {
            "surface": "control_plane_lifecycle_report",
            "workspace_roots": [str(path) for path in workspace_roots],
            "scan_policy": {
                "deep_scan_enabled": deep,
                "max_files": max_files,
                "max_seconds": max_seconds,
            },
        },
    )

    payload = module.MedAutoScienceDomainEntry().dispatch(
        {
            "command": "control-plane-lifecycle-report",
            "workspace_roots": [str(workspace_root)],
            "deep": True,
            "max_files": 13,
            "max_seconds": 3.25,
        }
    )

    assert payload == {
        "command": "control-plane-lifecycle-report",
        "surface": "control_plane_lifecycle_report",
        "workspace_roots": [str(workspace_root)],
        "scan_policy": {
            "deep_scan_enabled": True,
            "max_files": 13,
            "max_seconds": 3.25,
        },
    }


def test_domain_entry_dispatches_cleanup_apply_control_plane_snapshot(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")
    workspace_root = tmp_path / "workspace"
    snapshot = {"surface": "control_plane_snapshot"}
    captured: dict[str, object] = {}

    def fake_run_cleanup_apply(*, workspace_roots, apply, control_plane_snapshot=None):
        captured["workspace_roots"] = list(workspace_roots)
        captured["apply"] = apply
        captured["control_plane_snapshot"] = control_plane_snapshot
        return {
            "surface": "control_plane_cleanup_apply",
            "workspace_roots": [str(path) for path in workspace_roots],
            "apply": apply,
        }

    monkeypatch.setattr(module.control_plane_cleanup_apply, "run_cleanup_apply", fake_run_cleanup_apply)

    payload = module.MedAutoScienceDomainEntry().dispatch(
        {
            "command": "control-plane-cleanup-apply",
            "workspace_roots": [str(workspace_root)],
            "apply": True,
            "control_plane_snapshot": snapshot,
        }
    )

    assert captured == {
        "workspace_roots": [workspace_root],
        "apply": True,
        "control_plane_snapshot": snapshot,
    }
    assert payload["surface"] == "control_plane_cleanup_apply"


def test_domain_entry_dispatches_backfill_apply_control_plane_snapshot(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")
    workspace_root = tmp_path / "workspace"
    snapshot = {"surface": "control_plane_snapshot"}
    captured: dict[str, object] = {}

    def fake_run_backfill_apply(*, workspace_roots, apply, control_plane_snapshot=None):
        captured["workspace_roots"] = list(workspace_roots)
        captured["apply"] = apply
        captured["control_plane_snapshot"] = control_plane_snapshot
        return {
            "surface": "control_plane_backfill_apply",
            "workspace_roots": [str(path) for path in workspace_roots],
            "apply": apply,
        }

    monkeypatch.setattr(module.control_plane_backfill_apply, "run_backfill_apply", fake_run_backfill_apply)

    payload = module.MedAutoScienceDomainEntry().dispatch(
        {
            "command": "control-plane-backfill-apply",
            "workspace_roots": [str(workspace_root)],
            "apply": True,
            "control_plane_snapshot": snapshot,
        }
    )

    assert captured == {
        "workspace_roots": [workspace_root],
        "apply": True,
        "control_plane_snapshot": snapshot,
    }
    assert payload["surface"] == "control_plane_backfill_apply"


def test_domain_entry_contract_exports_domain_agent_entry_spec_v1() -> None:
    module = importlib.import_module("med_autoscience.domain_entry_contract")

    contract = module.build_domain_entry_contract()
    spec = contract["domain_agent_entry_spec"]

    assert spec["surface_kind"] == "domain_agent_entry_spec"
    assert spec["agent_id"] == "mas"
    assert spec["title"] == "MAS Domain Agent Entry (v1)"
    assert "可审计的入口与进度语义" in spec["description"]
    assert spec["default_engine"] == "codex"
    assert spec["workspace_requirement"] == "required"
    assert spec["locator_schema"] == {
        "required_fields": ["profile_ref"],
        "optional_fields": ["study_id", "entry_mode"],
    }
    assert spec["codex_entry_strategy"] == "domain_agent_entry"
    assert spec["artifact_conventions"] == "paper_and_submission_package"
    assert spec["progress_conventions"] == "study_runtime_narration"
    assert spec["entry_command"] == "product-entry-status"
    assert spec["manifest_command"] == "product-entry-manifest"
    assert contract["surface_role"] == "domain_handler_target_for_opl_generated_interfaces"
    assert contract["generated_descriptor_owner"] == "one-person-lab"
    assert contract["domain_handler_target_owner"] == "MedAutoScience"
    assert contract["domain_repo_can_own_generated_surface"] is False
    assert contract["authority_boundary"] == {
        "opl_owns_generated_cli_mcp_skill_product_status_workbench_descriptors": True,
        "mas_executes_domain_handlers_and_signs_owner_receipts": True,
        "opl_can_write_domain_truth": False,
        "opl_can_authorize_quality_or_export": False,
    }


def _build_request_from_contract(
    domain_entry_contract: dict[str, object],
    command: str,
    **context: str,
) -> dict[str, str]:
    for item in domain_entry_contract["command_contracts"]:
        if item["command"] == command:
            request = {"command": command}
            for field in item["required_fields"] + item["optional_fields"]:
                value = context.get(field)
                if value is not None:
                    request[field] = value
            missing_fields = [field for field in item["required_fields"] if field not in request]
            if missing_fields:
                raise AssertionError(f"external caller context 缺少字段: {missing_fields}")
            return request
    raise AssertionError(f"未找到 command contract: {command}")
