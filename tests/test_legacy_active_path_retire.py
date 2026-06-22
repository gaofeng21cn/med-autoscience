from __future__ import annotations

import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


REPO_ROOT = Path(__file__).resolve().parents[1]
LEGACY_SURFACE_ID = "dhd_owner_route_dispatch_paper_recovery_default_paper_mainline"


def _legacy_tombstone() -> dict[str, object]:
    contract = json.loads(
        (REPO_ROOT / "contracts/runtime/legacy-active-path-tombstones.json").read_text(
            encoding="utf-8"
        )
    )
    surfaces = {item["surface_id"]: item for item in contract["tombstoned_surfaces"]}
    return surfaces[LEGACY_SURFACE_ID]


def test_old_dhd_owner_route_dispatch_recovery_path_is_not_default_mainline() -> None:
    tombstone = _legacy_tombstone()

    assert tombstone["classification"] == "diagnostics_migration_provenance_only"
    assert tombstone["default_caller"] is False
    assert tombstone["default_product_mainline_claim_allowed"] is False
    assert tombstone["default_domain_handler_mainline_claim_allowed"] is False
    assert set(tombstone["legacy_surfaces"]) >= {
        "domain_health_diagnostic",
        "DHD",
        "owner-route",
        "owner_route",
        "domain-handler export",
        "default-executor dispatch",
        "dispatch",
        "PaperRecovery",
        "paper_recovery_state",
    }


def test_old_path_replacement_points_to_paper_mission_run_contract() -> None:
    tombstone = _legacy_tombstone()

    assert tombstone["replacement_ref"] == "contracts/paper_mission_run_contract.json"
    assert tombstone["replacement_projection_ref"] == (
        "study_progress.artifact_first_mission_summary.paper_mission_run"
    )
    assert tombstone["replacement_contract"] == {
        "contract_ref": "contracts/paper_mission_run_contract.json",
        "schema_version": "paper-mission-run.v1",
        "validator": "med_autoscience.paper_mission_run.PaperMissionRun",
        "projection_ref": "artifact_first_mission_summary.paper_mission_run",
    }
    assert tombstone["replacement_parity_proof"] == {
        "status": "machine_proved",
        "replacement_action_intent": "paper_mission/start_or_resume",
        "product_entry_surface": "medical_paper_product_entry",
        "product_entry_default_command_contains": "paper-mission inspect",
        "domain_handler_default_task_kind": "paper_mission/start_or_resume",
        "study_progress_default_projection": "artifact_first_mission_summary.paper_mission_run",
        "legacy_task_kind_policy": {
            "task_kind": "domain_owner/default-executor-dispatch",
            "default_paper_mission_entry": False,
            "migration_diagnostic_only": True,
            "active_caller_class": "diagnostic_only",
        },
    }


def test_old_path_forbidden_claims_include_progress_and_dm_completion() -> None:
    tombstone = _legacy_tombstone()

    assert set(tombstone["forbidden_default_claims"]) >= {
        "product_default_mainline",
        "domain_handler_default_mainline",
        "paper_progress",
        "publication_ready",
        "submission_ready",
        "runtime_ready",
        "provider_running",
        "owner_receipt_written",
        "typed_blocker_written",
        "current_package",
        "DM002_complete",
        "DM003_complete",
    }
    assert tombstone["authority_boundary"] == {
        "read_only": True,
        "history_provenance_only": True,
        "diagnostics_only": True,
        "migration_input_only": True,
        "can_write_domain_truth": False,
        "can_authorize_publication_quality": False,
        "can_authorize_artifact_mutation": False,
        "can_authorize_provider_admission": False,
        "can_claim_paper_progress": False,
        "can_claim_publication_ready": False,
        "can_claim_runtime_ready": False,
        "can_claim_dm002_complete": False,
        "can_claim_dm003_complete": False,
    }


def test_no_active_default_caller_proof_scope_is_explicit() -> None:
    contract = json.loads(
        (REPO_ROOT / "contracts/runtime/legacy-active-path-tombstones.json").read_text(
            encoding="utf-8"
        )
    )
    proof = contract["no_active_default_caller_proof"]

    assert proof["active_default_callers"] == []
    assert proof["default_cli_mcp_product_entry_or_skill_caller_count"] == 0
    assert proof["default_mainline_replacement"] == {
        "action_intent": "paper_mission/start_or_resume",
        "product_entry_surface": "medical_paper_product_entry",
        "domain_handler_task_kind": "paper_mission/start_or_resume",
        "contract_ref": "contracts/paper_mission_run_contract.json",
        "study_progress_projection": "artifact_first_mission_summary.paper_mission_run",
    }
    assert proof["readback_proof"] == {
        "status": "machine_proved",
        "surfaces": [
            "product_entry_manifest.medical_paper_product_entry",
            "domain_handler_export.dispatch",
            "domain_handler_export.pending_family_tasks",
            "study_progress.artifact_first_mission_summary",
        ],
        "required_shared_replacement": {
            "action_intent": "paper_mission/start_or_resume",
            "contract_ref": "contracts/paper_mission_run_contract.json",
            "schema_version": "paper-mission-run.v1",
            "validator": "med_autoscience.paper_mission_run.PaperMissionRun",
        },
        "legacy_active_caller_allowed_only_when": {
            "task_kind": "domain_owner/default-executor-dispatch",
            "default_paper_mission_entry": False,
            "migration_diagnostic_only": True,
            "active_caller_class": "diagnostic_only",
        },
    }
    assert proof["physical_reference_deletion_required_for_default_retirement"] is False
    assert set(proof["allowed_legacy_reference_classes"]) >= {
        "runtime diagnostic",
        "authority consume/readback",
        "OPL StageRun ABI carrier",
        "migration diagnostic",
        "history provenance",
        "legacy fixture",
    }

    scope_by_id = {item["surface_id"]: item for item in proof["proof_scope"]}
    assert set(scope_by_id) == {
        "product_entry_manifest.medical_paper_product_entry",
        "domain_handler_export.dispatch",
        "domain_handler_export.pending_family_tasks",
        "family_action_catalog",
        "mcp_tool_manifest",
        "plugin_skill_ordinary_path",
    }
    assert (
        scope_by_id["product_entry_manifest.medical_paper_product_entry"][
            "required_default_fields"
        ]["default_action_intent"]
        == "paper_mission/start_or_resume"
    )
    assert scope_by_id["domain_handler_export.dispatch"]["legacy_carrier_policy"] == {
        "task_kind": "domain_owner/default-executor-dispatch",
        "default_paper_mission_entry": False,
        "migration_diagnostic_only": True,
    }
    assert scope_by_id["plugin_skill_ordinary_path"]["required_ordinary_path"] == (
        "study -> stage -> domain owner receipt or typed blocker -> handoff"
    )


def test_domain_handler_default_mainline_has_no_legacy_dispatch_active_caller(
    tmp_path: Path,
) -> None:
    from med_autoscience.controllers import owner_route_handoff

    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "002-dm-china-us-mortality-attribution",
        quest_id="002-dm-china-us-mortality-attribution",
    )

    export = owner_route_handoff.export_family_domain_handler(
        profile=profile,
        profile_ref=tmp_path / "profile.toml",
    )

    assert export["dispatch"]["default_action_intent"] == "paper_mission/start_or_resume"
    assert "domain_owner/default-executor-dispatch" in export["dispatch"]["allowed_task_kinds"]
    assert export["legacy_default_executor_dispatch_diagnostics"] == []

    default_tasks = [
        task
        for task in export["pending_family_tasks"]
        if task.get("default_paper_mission_entry") is True
    ]
    assert [task["task_kind"] for task in default_tasks] == ["paper_mission/start_or_resume"]
    assert all(task.get("migration_diagnostic_only") is False for task in default_tasks)

    legacy_tasks = [
        task
        for task in export["pending_family_tasks"]
        if task.get("task_kind") == "domain_owner/default-executor-dispatch"
    ]
    assert all(task.get("default_paper_mission_entry") is False for task in legacy_tasks)
    assert all(task.get("migration_diagnostic_only") is True for task in legacy_tasks)
    assert all(task.get("active_caller_class") == "diagnostic_only" for task in legacy_tasks)


def test_legacy_default_executor_dispatch_task_is_demoted_when_carried() -> None:
    from med_autoscience.controllers.owner_route_handoff_parts import domain_handler_export

    marked = domain_handler_export._mark_legacy_default_executor_tasks(
        [
            {
                "task_kind": "domain_owner/default-executor-dispatch",
            },
            {
                "task_kind": "paper_mission/start_or_resume",
                "default_paper_mission_entry": True,
                "migration_diagnostic_only": False,
            },
        ]
    )

    legacy_task, paper_mission_task = marked
    assert legacy_task == {
        "task_kind": "domain_owner/default-executor-dispatch",
        "action_intent": "legacy_default_executor_diagnostic",
        "default_paper_mission_entry": False,
        "migration_diagnostic_only": True,
        "active_caller_class": "diagnostic_only",
    }
    assert paper_mission_task == {
        "task_kind": "paper_mission/start_or_resume",
        "default_paper_mission_entry": True,
        "migration_diagnostic_only": False,
    }


def test_product_entry_default_mainline_has_no_legacy_dhd_or_dispatch_command(
    tmp_path: Path,
) -> None:
    from med_autoscience.controllers import product_entry

    profile = make_profile(tmp_path)

    manifest = product_entry.build_product_entry_manifest(
        profile=profile,
        profile_ref=tmp_path / "profile.toml",
    )

    paper_mission = manifest["medical_paper_product_entry"]
    default_command = paper_mission["default_command"]
    assert paper_mission["default_action_intent"] == "paper_mission/start_or_resume"
    assert "paper-mission inspect" in default_command
    assert "domain-health-diagnostic" not in default_command
    assert "default-executor-dispatch" not in default_command
    assert "PaperRecovery" not in default_command


def test_action_catalog_and_mcp_manifest_do_not_expose_legacy_default_paper_tool(
    tmp_path: Path,
) -> None:
    from med_autoscience import action_catalog, mcp_server

    profile_ref = tmp_path / "profile.toml"
    catalog = action_catalog.build_mas_action_catalog(profile_ref=profile_ref)
    neutral_catalog = action_catalog.build_mas_action_catalog()

    actions = {item["action_id"]: item for item in catalog["actions"]}
    assert {
        "domain_health_diagnostic",
        "domain-health-diagnostic",
        "default_executor_dispatch",
        "default-executor-dispatch",
        "paper_recovery",
        "PaperRecovery",
    }.isdisjoint(actions)

    legacy_markers = (
        "PaperRecovery",
        "domain-health-diagnostic",
        "default-executor-dispatch",
    )
    for projection in ("cli", "product_entry", "skill", "mcp"):
        projected = action_catalog.project_mas_action_catalog(
            projection,
            catalog if projection != "mcp" else neutral_catalog,
        )
        serialized = json.dumps(projected, ensure_ascii=False)
        for marker in legacy_markers:
            assert marker not in serialized

    mcp_tool_names = {tool["name"] for tool in mcp_server.build_tool_manifest()}
    assert {
        "domain_health_diagnostic",
        "domain-health-diagnostic",
        "default_executor_dispatch",
        "default-executor-dispatch",
        "paper_recovery",
        "PaperRecovery",
        "domain_handler_export",
        "domain_handler_dispatch",
    }.isdisjoint(mcp_tool_names)

    mcp_projection = {
        item["name"]: item
        for item in action_catalog.project_mas_action_catalog("mcp", neutral_catalog)
    }
    assert mcp_projection["domain_handler_export"]["descriptor_only"] is True
    assert mcp_projection["domain_handler_export"]["public_runtime"] is False
    assert mcp_projection["domain_handler_dispatch"]["descriptor_only"] is True
    assert mcp_projection["domain_handler_dispatch"]["public_runtime"] is False

    assert {
        "doctor_audit",
        "workspace_readiness",
        "research_assets",
        "study_progress",
        "open_auto_research_soak",
        "publication_status",
        "display_pack_agent",
        "scientific_capability_registry",
        "authority_operations",
        "agent_tool_arsenal",
    } == set(mcp_server.TOOL_HANDLERS)


def test_plugin_skill_ordinary_path_does_not_use_legacy_default_paper_mainline() -> None:
    skill_text = (REPO_ROOT / "plugins/mas/skills/mas/SKILL.md").read_text(encoding="utf-8")
    ordinary_path_line = next(
        line for line in skill_text.splitlines() if line.startswith("Ordinary path:")
    )
    runtime_tick_line = next(
        line for line in skill_text.splitlines() if line.startswith("Runtime controller tick:")
    )

    assert ordinary_path_line == (
        "Ordinary path: study -> stage -> domain owner receipt or typed blocker -> handoff"
    )
    assert "domain-health-diagnostic" not in ordinary_path_line
    assert "default-executor-dispatch" not in ordinary_path_line
    assert "PaperRecovery" not in ordinary_path_line

    assert "domain-health-diagnostic" in runtime_tick_line
