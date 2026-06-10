from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study


@pytest.mark.parametrize("command", ("product-entry-status", "skill-catalog"))
def test_domain_entry_rejects_removed_public_wrapper_commands(command: str, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")
    profile_ref = tmp_path / "profile.local.toml"

    with pytest.raises(ValueError, match="不支持的 domain entry command"):
        module.MedAutoScienceDomainEntry().dispatch(
            {
                "command": command,
                "profile_ref": str(profile_ref),
            }
        )


def test_domain_entry_launch_study_forwards_explicit_user_wakeup(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    called: dict[str, object] = {}

    def fake_launch_study(
        *,
        profile,
        profile_ref,
        study_id: str,
        entry_mode: str | None,
        allow_stopped_relaunch: bool,
        explicit_user_wakeup: bool,
        force: bool,
    ) -> dict[str, object]:
        called["profile"] = profile
        called["profile_ref"] = profile_ref
        called["study_id"] = study_id
        called["entry_mode"] = entry_mode
        called["allow_stopped_relaunch"] = allow_stopped_relaunch
        called["explicit_user_wakeup"] = explicit_user_wakeup
        called["force"] = force
        return {"surface_kind": "launch_study", "runtime_status": {"decision": "resume"}}

    monkeypatch.setattr(module, "load_profile", lambda ref: profile)
    monkeypatch.setattr(module.product_entry, "launch_study", fake_launch_study)

    payload = module.MedAutoScienceDomainEntry().dispatch(
        {
            "command": "launch-study",
            "profile_ref": str(profile_ref),
            "study_id": "001-risk",
            "entry_mode": "full_research",
            "allow_stopped_relaunch": True,
            "explicit_user_wakeup": True,
            "force": True,
        }
    )

    assert payload["command"] == "launch-study"
    assert called["profile"] is profile
    assert called["profile_ref"] == profile_ref
    assert called["study_id"] == "001-risk"
    assert called["entry_mode"] == "full_research"
    assert called["allow_stopped_relaunch"] is True
    assert called["explicit_user_wakeup"] is True
    assert called["force"] is True


def test_external_caller_can_consume_domain_entry_contract_without_repo_local_helper(
    monkeypatch,
    tmp_path: Path,
) -> None:
    domain_entry_module = importlib.import_module("med_autoscience.domain_entry")
    contract_module = importlib.import_module("med_autoscience.domain_entry_contract")
    profile = make_profile(tmp_path)
    profile_ref = tmp_path / "profile.local.toml"
    write_study(profile.workspace_root, "001-risk")

    contract = contract_module.build_domain_entry_contract()

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


def test_domain_entry_dispatches_authority_operations(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")
    workspace_root = tmp_path / "workspace"

    monkeypatch.setattr(
        module.workspace_authority_migration_audit,
        "run_migration_audit",
        lambda *, workspace_roots, dry_run: {
            "surface": "workspace_authority_migration_audit",
            "workspace_roots": [str(path) for path in workspace_roots],
            "dry_run": dry_run,
        },
    )

    payload = module.MedAutoScienceDomainEntry().dispatch(
        {
            "command": "workspace-authority-migration-audit",
            "workspace_roots": [str(workspace_root)],
        }
    )

    assert payload == {
        "command": "workspace-authority-migration-audit",
        "surface": "workspace_authority_migration_audit",
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
            "surface": "artifact_lifecycle_report",
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
            "command": "artifact-lifecycle-report",
            "workspace_roots": [str(workspace_root)],
            "deep": True,
            "max_files": 13,
            "max_seconds": 3.25,
        }
    )

    assert payload == {
        "command": "artifact-lifecycle-report",
        "surface": "artifact_lifecycle_report",
        "workspace_roots": [str(workspace_root)],
        "scan_policy": {
            "deep_scan_enabled": True,
            "max_files": 13,
            "max_seconds": 3.25,
        },
    }


def test_domain_entry_dispatches_display_pack_agent_plan_without_profile() -> None:
    module = importlib.import_module("med_autoscience.domain_entry")
    repo_root = Path(__file__).resolve().parents[1]

    payload = module.MedAutoScienceDomainEntry().dispatch(
        {
            "command": "display-pack-figure-plan",
            "repo_root": str(repo_root),
            "figure_request": {
                "figure_kind": "evidence_figure",
                "audit_family": "Prediction Performance",
                "preferred_renderer_family": "r_ggplot2",
                "query": "roc",
            },
        }
    )

    assert payload["command"] == "display-pack-figure-plan"
    assert payload["surface_kind"] == "display_pack_agent_figure_plan"
    assert payload["recommended_template"]["template_id"] == "roc_curve_binary"
    assert payload["authority_boundary"]["can_authorize_publication_readiness"] is False


def test_domain_entry_contract_exports_display_pack_agent_commands() -> None:
    contract_module = importlib.import_module("med_autoscience.domain_entry_contract")

    contracts = {
        item["command"]: item
        for item in contract_module.build_domain_entry_contract()["command_contracts"]
    }

    assert contracts["display-pack-capability-discover"]["optional_fields"] == [
        "repo_root",
        "paper_root",
        "include_templates",
    ]
    assert contracts["display-pack-figure-plan"]["required_fields"] == ["figure_request"]
    assert contracts["display-pack-render"]["required_fields"] == ["paper_root"]
    assert "visual_audit_review" in contracts["display-pack-render"]["optional_fields"]


def test_domain_entry_rejects_control_plane_cleanup_apply(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")
    workspace_root = tmp_path / "workspace"

    with pytest.raises(ValueError, match="不支持的 domain entry command"):
        module.MedAutoScienceDomainEntry().dispatch({
            "command": "control-plane-cleanup-apply",
            "workspace_roots": [str(workspace_root)],
            "apply": True,
        })


def test_domain_entry_dispatches_backfill_apply_authority_snapshot(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.domain_entry")
    workspace_root = tmp_path / "workspace"
    snapshot = {"surface": "authority_snapshot"}
    captured: dict[str, object] = {}

    def fake_run_backfill_apply(*, workspace_roots, apply, authority_snapshot=None):
        captured["workspace_roots"] = list(workspace_roots)
        captured["apply"] = apply
        captured["authority_snapshot"] = authority_snapshot
        return {
            "surface": "delivery_authority_backfill_apply",
            "workspace_roots": [str(path) for path in workspace_roots],
            "apply": apply,
        }

    monkeypatch.setattr(module.delivery_authority_backfill_apply, "run_backfill_apply", fake_run_backfill_apply)

    payload = module.MedAutoScienceDomainEntry().dispatch(
        {
            "command": "delivery-authority-backfill-apply",
            "workspace_roots": [str(workspace_root)],
            "apply": True,
            "authority_snapshot": snapshot,
        }
    )

    assert captured == {
        "workspace_roots": [workspace_root],
        "apply": True,
        "authority_snapshot": snapshot,
    }
    assert payload["surface"] == "delivery_authority_backfill_apply"


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
    assert spec["entry_command"] == "study-progress"
    assert spec["manifest_command"] == "opl-generated-product-entry"
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
