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
        "product_entry_default_command_contains": "paper-mission drive",
        "domain_handler_default_task_kind": "paper_mission/start_or_resume",
        "study_progress_default_projection": "artifact_first_mission_summary.paper_mission_run",
        "legacy_task_kind_policy": {
            "task_kind": "domain_owner/default-executor-dispatch",
            "default_paper_mission_entry": False,
            "migration_diagnostic_only": True,
            "ordinary_schedulable": False,
            "active_caller_class": "diagnostic_only",
            "dispatch_fail_closed_reason": "legacy_default_executor_dispatch_tombstoned",
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
            "ordinary_schedulable": False,
            "active_caller_class": "diagnostic_only",
            "dispatch_fail_closed_reason": "legacy_default_executor_dispatch_tombstoned",
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
    rigor_policy = proof["legacy_reference_rigor_policy"]
    assert rigor_policy["status"] == "active_claim_boundary"
    assert rigor_policy["required_for_each_allowed_reference_class"] == [
        "reference_class",
        "allowed_use",
        "required_evidence",
        "forbidden_claims",
        "can_select_next_paper_stage",
        "counts_as_paper_progress",
        "can_claim_runtime_ready",
    ]
    assert set(rigor_policy["paper_progress_claim_requires"]) == {
        "PaperMissionRun_or_PaperMissionTransaction_artifact_delta",
        "MAS_owner_receipt_or_stable_typed_blocker_or_human_gate_or_route_back",
        "same_currentness_identity_binding",
    }
    assert set(rigor_policy["runtime_readiness_claim_requires"]) == {
        "OPL_StageRun_or_provider_attempt_readback",
        "same_route_attempt_identity",
        "no_forbidden_write_boundary",
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
        "ordinary_schedulable": False,
        "dispatch_fail_closed_reason": "legacy_default_executor_dispatch_tombstoned",
    }
    assert scope_by_id["domain_handler_export.pending_family_tasks"][
        "legacy_task_kind_allowed"
    ] is False
    assert scope_by_id["plugin_skill_ordinary_path"]["required_ordinary_path"] == (
        "study -> stage -> domain owner receipt or typed blocker -> handoff"
    )


def test_allowed_legacy_reference_classes_are_claim_limited() -> None:
    contract = json.loads(
        (REPO_ROOT / "contracts/runtime/legacy-active-path-tombstones.json").read_text(
            encoding="utf-8"
        )
    )
    proof = contract["no_active_default_caller_proof"]
    policy = proof["legacy_reference_rigor_policy"]

    claim_boundaries = {
        item["reference_class"]: item
        for item in policy["allowed_reference_claim_boundaries"]
    }
    assert set(claim_boundaries) == set(proof["allowed_legacy_reference_classes"])

    for reference_class, boundary in claim_boundaries.items():
        assert boundary["allowed_use"]
        assert boundary["required_evidence"], reference_class
        assert boundary["can_select_next_paper_stage"] is False, reference_class
        assert boundary["counts_as_paper_progress"] is False, reference_class
        assert boundary["can_claim_runtime_ready"] is False, reference_class
        assert "paper_progress" in boundary["forbidden_claims"], reference_class

    assert set(claim_boundaries["runtime diagnostic"]["required_evidence"]) == {
        "fresh_diagnostic_readback",
        "same_identity_boundary_or_explicit_stale_marker",
    }
    assert set(claim_boundaries["authority consume/readback"]["required_evidence"]) == {
        "consume_readback_payload",
        "written_files_empty_or_authority_surface_receipt_ref",
        "authority_materialized_flag",
    }
    assert set(claim_boundaries["OPL StageRun ABI carrier"]["required_evidence"]) == {
        "route_command_ref",
        "stage_terminal_decision_ref",
        "required_postcondition",
        "no_forbidden_write_boundary",
    }
    assert set(claim_boundaries["migration diagnostic"]["required_evidence"]) == {
        "legacy_truth_import_pack",
        "replacement_paper_mission_run_ref",
        "legacy_blocker_is_default_execution_state_false",
    }
    assert set(claim_boundaries["history provenance"]["required_evidence"]) == {
        "tombstone_ref",
        "history_or_provenance_ref",
    }
    assert set(claim_boundaries["legacy fixture"]["required_evidence"]) == {
        "fixture_scope",
        "replacement_parity_or_fail_closed_assertion",
    }


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
    assert export["dispatch"]["default_queue_source"] == "/paper_mission_default_tasks"
    assert export["dispatch"]["legacy_queue_source"] == "/pending_family_tasks"
    assert export["pending_family_tasks_policy"]["default_paper_mission_queue_source"] == (
        "/paper_mission_default_tasks"
    )
    assert export["pending_family_tasks_policy"]["non_default_task_policy"] == {
        "default_paper_mission_entry": False,
        "paper_mission_default_role": "diagnostic_or_explicit_owner_handoff",
        "can_select_next_paper_stage": False,
        "can_authorize_provider_admission": False,
        "counts_as_paper_progress": False,
    }
    assert "domain_owner/default-executor-dispatch" not in export["dispatch"]["allowed_task_kinds"]
    assert "domain_owner/default-executor-dispatch" in export["dispatch"][
        "legacy_diagnostic_task_kinds"
    ]
    assert export["legacy_default_executor_dispatch_diagnostics"] == []

    default_tasks = export["paper_mission_default_tasks"]
    assert [task["task_kind"] for task in default_tasks] == ["paper_mission/start_or_resume"]
    assert all(task.get("migration_diagnostic_only") is False for task in default_tasks)
    assert not [
        task
        for task in export["pending_family_tasks"]
        if task.get("default_paper_mission_entry") is True
    ]

    legacy_tasks = [
        task
        for task in export["pending_family_tasks"]
        if task.get("task_kind") == "domain_owner/default-executor-dispatch"
    ]
    assert legacy_tasks == []
    non_default_tasks = [
        task
        for task in export["pending_family_tasks"]
        if task.get("default_paper_mission_entry") is not True
    ]
    for task in non_default_tasks:
        assert task["paper_mission_default_role"] == "diagnostic_or_explicit_owner_handoff"
        assert task["can_select_next_paper_stage"] is False
        assert task["can_authorize_provider_admission"] is False
        assert task["counts_as_paper_progress"] is False


def test_domain_handler_dispatch_rejects_legacy_default_executor_task_kind(
    tmp_path: Path,
) -> None:
    from med_autoscience.controllers.owner_route_handoff_parts import dispatch_orchestration

    task_path = tmp_path / "legacy-default-executor-task.json"
    task_path.write_text(
        json.dumps(
            {
                "task_id": "legacy-dispatch-001",
                "domain_id": "medautoscience",
                "task_kind": "domain_owner/default-executor-dispatch",
                "payload": {
                    "profile": str(tmp_path / "profile.toml"),
                    "study_id": "001-paper",
                },
            }
        ),
        encoding="utf-8",
    )

    receipt = dispatch_orchestration.dispatch_family_domain_handler_task(
        task_path=task_path
    )

    assert receipt["accepted"] is False
    assert receipt["reason"] == "legacy_default_executor_dispatch_tombstoned"
    assert receipt["task_kind"] == "domain_owner/default-executor-dispatch"
    assert receipt["legacy_diagnostic_task_kind"] is True
    assert receipt["default_paper_mission_entry"] is False
    assert receipt["migration_diagnostic_only"] is True
    assert receipt["ordinary_schedulable"] is False
    assert receipt["active_caller_class"] == "diagnostic_only"
    assert receipt["replacement_task_kind"] == "paper_mission/start_or_resume"


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
        "ordinary_schedulable": False,
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
    assert "paper-mission drive" in default_command
    assert "paper-mission inspect" in paper_mission["inspect_command"]
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


def test_tracked_action_catalog_and_tool_arsenal_demote_domain_handler_dispatch() -> None:
    action_catalog = json.loads(
        (REPO_ROOT / "contracts/action_catalog.json").read_text(encoding="utf-8")
    )
    tool_arsenal = json.loads(
        (REPO_ROOT / "contracts/agent_tool_arsenal.json").read_text(encoding="utf-8")
    )

    actions = {item["action_id"]: item for item in action_catalog["actions"]}
    dispatch_action = actions["domain_handler_dispatch"]
    assert dispatch_action["effect"] == "mutating"
    assert "non-authority submission milestone candidate packages" in dispatch_action[
        "summary"
    ]
    assert "does not create owner receipts" in dispatch_action["summary"]
    assert "can only return diagnostic/fail-closed readback" in dispatch_action["summary"]

    tool_cards = {item["tool_id"]: item for item in tool_arsenal["tool_cards"]}
    dispatch_tool = tool_cards["domain_handler_dispatch"]
    assert dispatch_tool["effect"] == "mutating"
    assert dispatch_tool["allowed_writes"] == [
        "ops/medautoscience/paper_mission_candidate_package/<run_id>/**",
        "ops/medautoscience/paper_mission_consumption_ledger/<run_id>/**",
    ]
    assert dispatch_tool["authority_effects"]["can_return_owner_receipt"] is False
    assert dispatch_tool["authority_effects"]["can_return_typed_blocker"] is False
    assert dispatch_tool["authority_effects"]["owner_answer_surface"] == (
        "paper_mission_authority_consume_or_terminal_owner_gate"
    )
    assert dispatch_tool["invocation_gate"]["requires_opl_stage_attempt_or_lease"] is False
    assert dispatch_tool["invocation_gate"]["owner_receipt_or_typed_blocker_required"] is False
    assert dispatch_tool["non_read_only_gate"][
        "requires_owner_receipt_or_typed_blocker_proof"
    ] is False


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
