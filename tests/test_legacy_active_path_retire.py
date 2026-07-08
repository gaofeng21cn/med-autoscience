from __future__ import annotations

import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_study


REPO_ROOT = Path(__file__).resolve().parents[1]
LEGACY_SURFACE_ID = "domain_diagnostic_owner_route_dispatch_paper_recovery_default_paper_mainline"
LEGACY_NEXT_ACTION_SURFACE_ID = "legacy_next_action_projection_and_selector_surfaces"


def _tombstone(surface_id: str) -> dict[str, object]:
    contract = json.loads(
        (REPO_ROOT / "contracts/runtime/legacy-active-path-tombstones.json").read_text(
            encoding="utf-8"
        )
    )
    surfaces = {item["surface_id"]: item for item in contract["tombstoned_surfaces"]}
    return surfaces[surface_id]


def _legacy_tombstone() -> dict[str, object]:
    return _tombstone(LEGACY_SURFACE_ID)


def _legacy_next_action_tombstone() -> dict[str, object]:
    return _tombstone(LEGACY_NEXT_ACTION_SURFACE_ID)


def test_old_domain_diagnostic_owner_route_dispatch_recovery_path_is_not_default_mainline() -> None:
    tombstone = _legacy_tombstone()

    assert tombstone["classification"] == "retired_diagnostics_migration_provenance_only"
    assert tombstone["default_caller"] is False
    assert tombstone["default_product_mainline_claim_allowed"] is False
    assert tombstone["default_domain_handler_mainline_claim_allowed"] is False
    assert set(tombstone["legacy_surfaces"]) >= {
        "domain_diagnostic_report",
        "domain diagnostic",
        "owner-route",
        "owner_route",
        "domain-handler export",
        "owner-callable dispatch",
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
            "retired_task_kind_marker": "owner_callable_adapter_stage_run_abi_tombstoned",
            "default_paper_mission_entry": False,
            "migration_diagnostic_only": True,
            "ordinary_schedulable": False,
            "active_caller_class": "diagnostic_only",
            "dispatch_fail_closed_reason": "legacy_owner_callable_dispatch_tombstoned",
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
        "retired_tombstone": True,
        "active_public_projection_alias_allowed": False,
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


def test_legacy_next_action_projection_and_selector_surfaces_are_tombstoned() -> None:
    tombstone = _legacy_next_action_tombstone()

    assert tombstone["classification"] == "retired_next_action_diagnostics_provenance_only"
    assert tombstone["default_caller"] is False
    assert tombstone["default_next_action_selector_allowed"] is False
    assert tombstone["default_provider_admission_authority_allowed"] is False
    assert tombstone["replacement_projection_ref"] == "study_progress.next_action_envelope"
    assert tombstone["replacement_contract"] == {
        "contract_ref": "docs/runtime/control/next_action_control_plane.md",
        "machine_contract": "StageOutcome -> NextActionEnvelope",
        "transport_receipt_contract": "OPL TransitionReceipt is receipt-only evidence and MAS owner-consumption input",
        "canonical_projection_ref": "study_progress.next_action_envelope",
        "canonical_owner": "mas_next_action_compiler",
    }
    assert set(tombstone["legacy_surfaces"]) >= {
        "domain_next_action_projection",
        "current_executable_owner_action",
        "current_work_unit",
        "current_execution_envelope",
        "paper_recovery_state",
        "PaperRecovery",
        "domain_transition",
        "provider_admission",
        "managed_study_opl_provider_admission_candidates",
        "OPL queue",
        "OPL attempt",
        "control/next_action.json",
        "Stage Native next_action",
    }


def test_legacy_next_action_tombstone_forbids_default_authority_claims() -> None:
    contract = json.loads(
        (REPO_ROOT / "contracts/runtime/legacy-active-path-tombstones.json").read_text(
            encoding="utf-8"
        )
    )
    tombstone = _legacy_next_action_tombstone()

    assert {
        "current_work_unit",
        "current_executable_owner_action",
        "current_execution_envelope",
        "domain_next_action_projection",
        "Stage Native control/next_action.json",
        "provider admission as next-action selector",
        "OPL queue / attempt next-action inference",
    } <= set(contract["tombstone_index"]["retired_wording_families"])
    assert {
        "default next action selector",
        "provider admission authority",
        "submission-ready proof",
    } <= set(contract["tombstone_index"]["forbidden_use"])
    assert set(tombstone["forbidden_default_claims"]) >= {
        "default_next_action_selector",
        "provider_admission_authority",
        "paper_progress",
        "publication_ready",
        "submission_ready",
        "runtime_ready",
        "provider_running",
        "owner_receipt_written",
        "typed_blocker_written",
        "human_gate_written",
        "current_package",
        "DM002_complete",
        "DM003_complete",
    }
    assert tombstone["authority_boundary"] == {
        "read_only": True,
        "retired_tombstone": True,
        "history_provenance_only": True,
        "diagnostics_only": True,
        "migration_input_only": True,
        "can_select_default_next_action": False,
        "can_authorize_provider_admission": False,
        "can_write_domain_truth": False,
        "can_authorize_publication_quality": False,
        "can_authorize_artifact_mutation": False,
        "can_claim_paper_progress": False,
        "can_claim_publication_ready": False,
        "can_claim_submission_ready": False,
        "can_claim_runtime_ready": False,
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_write_human_gate": False,
        "can_claim_current_package": False,
        "can_claim_provider_running": False,
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
            "task_kind": "stage_outcome/opl-handoff",
            "default_paper_mission_entry": False,
            "migration_diagnostic_only": True,
            "ordinary_schedulable": False,
            "active_caller_class": "diagnostic_only",
            "dispatch_fail_closed_reason": "legacy_owner_callable_dispatch_tombstoned",
            "active_public_projection_alias_allowed": False,
        },
    }
    assert proof["physical_reference_deletion_required_for_default_retirement"] is False
    assert set(proof["allowed_legacy_reference_classes"]) >= {
        "runtime diagnostic",
        "authority consume/readback",
        "migration diagnostic",
        "history provenance",
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
        "task_kind": "stage_outcome/opl-handoff",
        "default_paper_mission_entry": False,
        "migration_diagnostic_only": True,
        "ordinary_schedulable": False,
        "dispatch_fail_closed_reason": "legacy_owner_callable_dispatch_tombstoned",
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
    assert set(claim_boundaries["migration diagnostic"]["required_evidence"]) == {
        "legacy_truth_import_pack",
        "replacement_paper_mission_run_ref",
        "legacy_blocker_is_default_execution_state_false",
    }
    assert set(claim_boundaries["history provenance"]["required_evidence"]) == {
        "tombstone_ref",
        "history_or_provenance_ref",
    }


def test_current_surface_legacy_wording_policy_blocks_authority_resurrection() -> None:
    contract = json.loads(
        (REPO_ROOT / "contracts/runtime/legacy-active-path-tombstones.json").read_text(
            encoding="utf-8"
        )
    )
    policy = contract["current_surface_wording_policy"]

    assert policy["status"] == "active_claim_boundary"
    assert "docs/history/**" in policy["excluded_scope"]
    assert {
        "docs/status.md",
        "docs/active/**",
        "docs/runtime/**",
        "product/read surface labels",
    } <= set(policy["scope"])
    assert {
        "current_work_unit",
        "current_executable_owner_action",
        "current_execution_envelope",
        "PaperRecovery",
        "provider admission",
        "queue / attempt",
        "StageAttempt",
        "control/next_action.json",
        "stage_native_workspace_next_action",
    } <= set(policy["legacy_terms"])
    assert {
        "diagnostic_only",
        "history_provenance_only",
        "retired_tombstone",
        "transport_observation",
        "no_resurrection_guard",
        "superseded_by_next_action_envelope",
    } == set(policy["required_context_markers"])
    assert policy["replacement_route"] == (
        "StageOutcome -> NextActionEnvelope -> OPL TransitionReceipt / MAS owner consumption"
    )
    assert {
        "default owner/action",
        "default next action selector",
        "provider admission authority",
        "delivery/submission completion",
        "paper progress",
        "publication-ready",
        "submission-ready",
        "runtime-ready",
        "current-package ready",
        "queue attempt success proof",
        "compatibility route",
    } == set(policy["forbidden_claims"])
    assert {
        "fresh paper-mission inspect or study_progress readback",
        "same-identity OPL StageRun or TransitionReceipt readback",
        "MAS owner receipt, stable typed blocker, human gate, route-back, artifact delta, or successor handoff",
    } == set(policy["evidence_required_for_live_acceptance"])
    assert policy["docs_or_tests_can_close_live_acceptance"] is False
    assert policy["can_select_default_next_action"] is False
    assert policy["can_claim_paper_progress"] is False
    assert policy["can_claim_runtime_ready"] is False
    assert policy["can_claim_submission_ready"] is False
    assert policy["can_claim_current_package_ready"] is False


def test_legacy_control_receipt_markers_are_filter_only_not_active_aliases() -> None:
    contract = json.loads(
        (REPO_ROOT / "contracts/runtime/legacy-active-path-tombstones.json").read_text(
            encoding="utf-8"
        )
    )
    policy = contract["legacy_control_receipt_exclusion_policy"]

    assert {
        "domain-health-diagnostic",
        "domain-diagnostic-report",
        "owner-route-reconcile",
        "default-executor",
        "workspace-local scheduler",
        "Hermes scheduler hosted runtime",
    } <= set(policy["legacy_markers"])
    assert policy["marker_alias_policy"] == {
        "legacy_markers_are_active_aliases": False,
        "legacy_markers_are_default_entrypoints": False,
        "legacy_markers_are_public_projection_aliases": False,
        "legacy_markers_can_claim_no_active_caller": False,
        "legacy_markers_can_satisfy_runtime_readiness": False,
        "legacy_markers_can_satisfy_paper_progress": False,
        "allowed_role": "duplicate_source_fingerprint_filter_marker_only",
    }
    assert policy["authority_boundary"] == {
        "read_only": True,
        "history_provenance_only": True,
        "can_create_runtime_entrypoint": False,
        "can_claim_generic_runtime_owner": False,
        "can_write_domain_truth": False,
        "can_authorize_publication_quality": False,
    }


def test_domain_handler_default_mainline_has_no_legacy_dispatch_active_caller(
    tmp_path: Path,
) -> None:
    from med_autoscience.controllers.owner_route_handoff import domain_handler_export

    profile = make_profile(tmp_path)
    write_study(
        profile.workspace_root,
        "002-dm-china-us-mortality-attribution",
        quest_id="002-dm-china-us-mortality-attribution",
    )

    export = domain_handler_export.export_family_domain_handler(
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
    assert "stage_outcome/opl-handoff" not in export["dispatch"]["allowed_task_kinds"]
    assert "domain_owner/owner-callable-adapter" in export["dispatch"][
        "retired_diagnostic_task_kinds"
    ]

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
        if task.get("task_kind") == "stage_outcome/opl-handoff"
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


def test_domain_handler_dispatch_rejects_legacy_owner_callable_adapter_task_kind(
    tmp_path: Path,
) -> None:
    from med_autoscience.controllers.owner_route_handoff import dispatch_orchestration

    task_path = tmp_path / "legacy-owner-callable-task.json"
    task_path.write_text(
        json.dumps(
            {
                "task_id": "legacy-dispatch-001",
                "domain_id": "medautoscience",
                "task_kind": "domain_owner/owner-callable-adapter",
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
    assert receipt["reason"] == "legacy_owner_callable_dispatch_tombstoned"
    assert receipt["task_kind"] == "domain_owner/owner-callable-adapter"
    assert receipt["retired_diagnostic_task_kind"] is True
    assert receipt["default_paper_mission_entry"] is False
    assert receipt["migration_diagnostic_only"] is True
    assert receipt["ordinary_schedulable"] is False
    assert receipt["active_caller_class"] == "diagnostic_only"
    assert receipt["replacement_task_kind"] == "paper_mission/start_or_resume"
    assert receipt["diagnostic_role"] == "retired_default_paper_dispatch"


def test_product_entry_default_mainline_has_no_legacy_domain_diagnostic_or_dispatch_command(
    tmp_path: Path,
) -> None:
    from med_autoscience.controllers.product_entry.manifest_surfaces import (
        build_product_entry_manifest,
    )

    profile = make_profile(tmp_path)

    manifest = build_product_entry_manifest(
        profile=profile,
        profile_ref=tmp_path / "profile.toml",
    )

    paper_mission = manifest["medical_paper_product_entry"]
    default_command = paper_mission["default_command"]
    assert paper_mission["default_action_intent"] == "paper_mission/start_or_resume"
    assert "paper-mission drive" in default_command
    assert "paper-mission inspect" in paper_mission["inspect_command"]
    assert "domain-diagnostic-report" not in default_command
    assert "owner-callable-adapter" not in default_command
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
        "domain_diagnostic_report",
        "domain-diagnostic-report",
        "owner_callable_dispatch",
        "owner-callable-adapter",
        "paper_recovery",
        "PaperRecovery",
    }.isdisjoint(actions)

    legacy_markers = (
        "PaperRecovery",
        "domain-diagnostic-report",
        "owner-callable-adapter",
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
        "domain_diagnostic_report",
        "domain-diagnostic-report",
        "owner_callable_dispatch",
        "owner-callable-adapter",
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
    skill_text = (REPO_ROOT / "plugins/med-autoscience/skills/med-autoscience/SKILL.md").read_text(encoding="utf-8")
    ordinary_path_line = next(
        line for line in skill_text.splitlines() if line.startswith("Ordinary path:")
    )
    runtime_control_line = next(
        line
        for line in skill_text.splitlines()
        if line.startswith("Paper mission readback/control surface:")
    )

    assert ordinary_path_line == (
        "Ordinary path: study -> stage -> domain owner receipt or typed blocker -> handoff"
    )
    assert "domain-diagnostic-report" not in ordinary_path_line
    assert "owner-callable-adapter" not in ordinary_path_line
    assert "PaperRecovery" not in ordinary_path_line

    assert "paper-mission inspect" in runtime_control_line
    assert "domain-diagnostic-report" not in runtime_control_line
