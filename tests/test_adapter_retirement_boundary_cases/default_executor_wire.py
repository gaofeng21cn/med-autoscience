from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src" / "med_autoscience"


def test_default_executor_dispatch_residue_cleanup_surface_is_physically_retired() -> None:
    assert not (
        SRC_ROOT / "controllers" / "default_executor_dispatch_residue_cleanup.py"
    ).exists()
    assert not (REPO_ROOT / "tests" / "test_default_executor_dispatch_residue_cleanup.py").exists()

    cli_text = (SRC_ROOT / "cli.py").read_text(encoding="utf-8")
    parser_text = (SRC_ROOT / "cli_parts" / "parser.py").read_text(encoding="utf-8")
    assert "_load_controller(\"default_executor_dispatch_residue_cleanup\")" not in cli_text
    assert "default_executor_dispatch_residue_cleanup =" not in cli_text
    assert "args.command == \"default-executor-dispatch-residue-cleanup\"" not in cli_text
    assert "add_parser(\"default-executor-dispatch-residue-cleanup\"" not in parser_text


def test_open_runtime_surfaces_cannot_use_active_callers_as_retention_reason() -> None:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    open_surfaces = [
        surface
        for surface in inventory["surfaces"]
        if surface["current_disposition"] != "physically_retired"
    ]

    assert open_surfaces
    for surface in open_surfaces:
        assert surface["compatibility_alias_allowed"] is False
        assert surface["mas_owner_claim_allowed"] is False
        assert "legacy_caller_exists" not in str(surface.get("retention_reason", ""))
        if surface["surface_id"] in {
            "domain_action_request_materializer_owner_callable_adapter_projection",
            "domain_owner_action_dispatch",
        }:
            gate = surface["retirement_gate"]
            assert gate["active_caller_alone_retains_surface"] is False
            assert gate["completion_claim_requires_live_owner_or_opl_readback"] is True
            assert gate["no_active_caller_required_before_physical_delete"] is True
            assert gate["no_forbidden_write_proof_required"] is True
            assert gate["replacement_parity_required"] is True
            assert gate["tombstone_or_provenance_required"] is True


def test_owner_callable_receipt_latest_reader_ignores_legacy_latest_wire(tmp_path) -> None:
    candidates = importlib.import_module(
        "med_autoscience.controllers.study_transition_receipt_consumption_parts.default_executor_candidates"
    )
    study_root = tmp_path / "studies" / "study-1"
    canonical_path = study_root / "artifacts" / "supervision" / "consumer" / "owner_callable_adapter_receipts" / "latest.json"
    legacy_path = study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json"
    legacy_path.parent.mkdir(parents=True)
    legacy_path.write_text(
        json.dumps(
            {
                "surface": "default_executor_dispatch_execution_study_latest",
                "executions": [
                    {
                        "surface": "default_executor_dispatch_execution",
                        "execution_status": "blocked",
                        "action_type": "legacy_action",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    canonical_path.parent.mkdir(parents=True)
    canonical_path.write_text(
        json.dumps(
            {
                "surface": "owner_callable_adapter_receipt_study_latest",
                "executions": [
                    {
                        "surface": "owner_callable_adapter_receipt",
                        "execution_status": "blocked",
                        "action_type": "canonical_action",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    payload, receipt_ref = candidates.latest_owner_callable_adapter_receipt_payload(study_root=study_root)

    assert receipt_ref == "artifacts/supervision/consumer/owner_callable_adapter_receipts/latest.json"
    assert payload["executions"][0]["action_type"] == "canonical_action"
    assert payload["executions"][0]["canonical_surface"] == "owner_callable_adapter_receipt"
    assert payload["projection_authority"] is False
    assert payload["queue_authority"] is False

    canonical_path.unlink()
    payload, receipt_ref = candidates.latest_owner_callable_adapter_receipt_payload(study_root=study_root)

    assert payload is None
    assert receipt_ref == "artifacts/supervision/consumer/owner_callable_adapter_receipts/latest.json"
    assert candidates.default_executor_execution_candidates(study_root=study_root) == []

def test_retired_legacy_stage_run_abi_scan_remains_provenance_not_delete_blocker() -> None:
    inventory = json.loads(
        (REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json").read_text(
            encoding="utf-8"
        )
    )
    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )
    surface = {
        item["surface_id"]: item for item in inventory["surfaces"]
    }["default_executor_execution_latest_wire_projection"]
    scan = surface["legacy_stage_run_abi_boundary"]["active_stage_run_abi_caller_scan"]

    assert surface["current_disposition"] == "physically_retired"
    assert surface["retirement_gate"] == {
        "active_caller_alone_retains_surface": False,
        "live_runtime_readiness_required_for_repo_source_delete": False,
        "no_forbidden_write_proof_proven": True,
        "replacement_parity_proven": True,
        "repo_source_physical_retirement_authorized": True,
        "tombstone_or_provenance_proven": True,
    }
    assert surface["tombstone_or_provenance_ref"] == (
        "docs/history/runtime/mas-private-surface-retirement.md#"
        "default_executor_execution_latest_wire_projection"
    )
    assert scan["status"] == "active_callers_present_tail_open"
    assert scan["no_active_stage_run_abi_caller_proven"] is False
    assert scan["physical_delete_allowed"] is False
    assert (
        scan["required_before_physical_delete"]
        == "legacy_default_executor_carrier_no_active_stage_run_abi_caller_physical_delete_ref"
    )
    assert {
        (
            "study_transition_receipt_consumption_parts.default_executor_candidates."
            "default_executor_execution_candidates::_stage_closeout_candidates"
        ),
        "study_transition_receipt_consumption.default_executor_execution_receipt_consumption",
        "study_transition_receipt_consumption.default_executor_execution_nonconsumable_closeout",
        "domain_health_diagnostic_parts.provider_admission_report_closeout_scan",
        "study_progress_parts.opl_current_control_state_terminal_logs",
    } <= set(scan["active_callers"])
    assert "terminal_closeout_consumption" in scan["allowed_consumption"]
    assert "typed_blocker_consumption" in scan["allowed_consumption"]
    assert "owner_route_currentness_identity_recovery" in scan["allowed_consumption"]
    assert "stage_closeout_provenance_only_as_physical_delete" in scan[
        "forbidden_completion_claims"
    ]

    audit = retirement.audit_runtime_surface_retirement_inventory(inventory)
    assert "default_executor_execution_latest_wire_projection" not in audit["open_surface_ids"]
    assert audit["repo_source_retirement_completion"]["completion_claim_allowed"] is True
    assert audit["completion_claim_allowed"] is True
    assert audit["live_runtime_readiness_completion"]["completion_claim_allowed"] is False

    bad_inventory = json.loads(json.dumps(inventory))
    bad_surface = {
        item["surface_id"]: item for item in bad_inventory["surfaces"]
    }["default_executor_execution_latest_wire_projection"]
    del bad_surface["tombstone_or_provenance_ref"]

    violations = retirement.validate_runtime_surface_retirement_inventory(bad_inventory)

    assert {
        (
            "default_executor_execution_latest_wire_projection",
            "physically_retired_missing_tombstone_or_provenance_ref",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in violations}


def test_domain_owner_dispatch_execution_latest_payload_ignores_legacy_opt_in(
    tmp_path,
) -> None:
    execution_io = importlib.import_module(
        "med_autoscience.controllers.domain_owner_action_dispatch_parts.execution_io"
    )
    profiles = importlib.import_module("med_autoscience.profiles")
    profile = profiles.WorkspaceProfile(
        name="test",
        workspace_root=tmp_path,
        runtime_root=tmp_path / "runtime",
        studies_root=tmp_path / "studies",
        portfolio_root=tmp_path / "portfolio",
        med_deepscientist_runtime_root=tmp_path / "legacy-runtime",
        med_deepscientist_repo_root=None,
        default_publication_profile="default",
        default_citation_style="vancouver",
        enable_medical_overlay=False,
        medical_overlay_scope="none",
        medical_overlay_skills=(),
        research_route_bias_policy="none",
        preferred_study_archetypes=(),
        default_submission_targets=(),
    )
    legacy_path = (
        profile.studies_root
        / "study-1"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json"
    )
    legacy_path.parent.mkdir(parents=True)
    legacy_path.write_text(
        json.dumps(
            {
                "surface": "default_executor_dispatch_execution_study_latest",
                "executions": [
                    {
                        "surface": "default_executor_dispatch_execution",
                        "execution_status": "blocked",
                        "action_type": "legacy_action",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert execution_io.execution_latest_payload(profile, "study-1") is None

    assert execution_io.execution_latest_payload(
        profile,
        "study-1",
        allow_legacy_fallback=True,
    ) is None


def test_domain_owner_dispatch_persist_does_not_merge_legacy_wire(
    tmp_path,
) -> None:
    dispatch_module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    profiles = importlib.import_module("med_autoscience.profiles")
    profile = profiles.WorkspaceProfile(
        name="test",
        workspace_root=tmp_path,
        runtime_root=tmp_path / "runtime",
        studies_root=tmp_path / "studies",
        portfolio_root=tmp_path / "portfolio",
        med_deepscientist_runtime_root=tmp_path / "legacy-runtime",
        med_deepscientist_repo_root=None,
        default_publication_profile="default",
        default_citation_style="vancouver",
        enable_medical_overlay=False,
        medical_overlay_scope="none",
        medical_overlay_skills=(),
        research_route_bias_policy="none",
        preferred_study_archetypes=(),
        default_submission_targets=(),
    )
    legacy_path = (
        profile.studies_root
        / "study-1"
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_execution"
        / "latest.json"
    )
    legacy_path.parent.mkdir(parents=True)
    legacy_path.write_text(
        json.dumps(
            {
                "surface": "default_executor_dispatch_execution_study_latest",
                "executions": [
                    {
                        "surface": "default_executor_dispatch_execution",
                        "execution_status": "blocked",
                        "action_type": "legacy_action",
                        "execution_id": "legacy-execution",
                        "study_id": "study-1",
                        "quest_id": "study-1",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    written = dispatch_module._persist_study_executions(
        profile=profile,
        study_id="study-1",
        generated_at="2026-06-19T00:00:00+00:00",
        study_executions=[
            {
                "surface": "owner_callable_adapter_receipt",
                "execution_status": "blocked",
                "action_type": "canonical_action",
                "execution_id": "canonical-execution",
                "study_id": "study-1",
                "quest_id": "study-1",
            }
        ],
    )

    latest_path = Path(written[0])
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    ledger = {item["execution_id"]: item for item in latest["execution_ledger"]}
    assert set(ledger) == {"canonical-execution"}
    assert latest["projection_authority"] is False
    assert latest["execution_ledger_authority"] is False
    assert latest["attempt_lifecycle_authority"] is False
    assert latest["queue_authority"] is False
    assert latest["executions"][0]["domain_authority_ref_index"]["status"] == (
        "opl_state_index_source_adapter_emitted"
    )


def test_current_owner_callable_readers_do_not_consume_legacy_latest_wire(tmp_path) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    export_projection = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.export_study_projection"
    )
    recovery_actions = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.recovery_actions"
    )
    study_root = tmp_path / "studies" / "study-1"
    legacy_path = study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json"
    legacy_execution = {
        "surface": "default_executor_dispatch_execution",
        "study_id": "study-1",
        "quest_id": "study-1",
        "execution_status": "handoff_ready",
        "provider_attempt_or_lease_required": True,
        "owner_callable_surface": "opl_default_executor.stage_attempt",
        "owner_route_current": True,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "fingerprint-legacy",
        "action_fingerprint": "fingerprint-legacy",
        "dispatch_path": "artifacts/supervision/consumer/default_executor_dispatches/immutable/run_quality_repair_batch/fingerprint-legacy.json",
        "dispatch_ref": "artifacts/supervision/consumer/default_executor_dispatches/immutable/run_quality_repair_batch/fingerprint-legacy.json",
        "owner_route": {
            "source_refs": {
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "fingerprint-legacy",
                "owner_route_currentness_basis": {
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "fingerprint-legacy",
                },
            }
        },
    }
    legacy_path.parent.mkdir(parents=True)
    legacy_path.write_text(
        json.dumps(
            {
                "surface": "default_executor_dispatch_execution_study_latest",
                "executions": [legacy_execution],
                "execution_ledger": [
                    {
                        "surface": "default_executor_dispatch_execution",
                        "execution_status": "blocked",
                        "action_type": "canonical_paper_inputs_rehydrate_required",
                        "blocked_reason": "canonical_paper_inputs_rehydrate_failed",
                        "next_owner": "write",
                        "owner_callable_surface": "legacy.rehydrate",
                        "required_input_surface": "legacy-input.json",
                        "required_output_surface": str(
                            study_root / "paper" / "legacy_medical_manuscript_blueprint_source.json"
                        ),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert provider_admission.persisted_provider_admission_candidates(
        study_root=study_root,
        status_payload={
            "study_id": "study-1",
            "current_executable_owner_action": {
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "fingerprint-legacy",
            },
        },
    ) == []
    assert export_projection._current_provider_handoff_execution(
        study_root=study_root,
        action_type="run_quality_repair_batch",
        work_unit_id="medical_prose_write_repair",
    ) == {}
    assert recovery_actions._latest_clean_migration_rehydrate_execution(study_root) is None


def test_legacy_latest_readers_consume_canonical_owner_callable_receipt_first(tmp_path) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    export_projection = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.export_study_projection"
    )
    recovery_actions = importlib.import_module(
        "med_autoscience.controllers.owner_route_reconcile_parts.recovery_actions"
    )
    study_root = tmp_path / "studies" / "study-1"
    canonical_path = study_root / "artifacts" / "supervision" / "consumer" / "owner_callable_adapter_receipts" / "latest.json"
    legacy_path = study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json"
    canonical_execution = {
        "surface": "owner_callable_adapter_receipt",
        "study_id": "study-1",
        "quest_id": "study-1",
        "execution_status": "handoff_ready",
        "provider_attempt_or_lease_required": True,
        "owner_callable_surface": "opl_default_executor.stage_attempt",
        "owner_route_current": True,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "fingerprint-current",
        "action_fingerprint": "fingerprint-current",
        "dispatch_path": "artifacts/supervision/consumer/default_executor_dispatches/immutable/run_quality_repair_batch/fingerprint-current.json",
        "dispatch_ref": "artifacts/supervision/consumer/default_executor_dispatches/immutable/run_quality_repair_batch/fingerprint-current.json",
        "owner_route": {
            "source_refs": {
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "fingerprint-current",
                "owner_route_currentness_basis": {
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "fingerprint-current",
                },
            }
        },
    }
    legacy_execution = {
        **canonical_execution,
        "surface": "default_executor_dispatch_execution",
        "work_unit_fingerprint": "fingerprint-legacy",
        "action_fingerprint": "fingerprint-legacy",
        "dispatch_path": "artifacts/supervision/consumer/default_executor_dispatches/immutable/run_quality_repair_batch/fingerprint-legacy.json",
        "dispatch_ref": "artifacts/supervision/consumer/default_executor_dispatches/immutable/run_quality_repair_batch/fingerprint-legacy.json",
    }
    canonical_path.parent.mkdir(parents=True)
    canonical_path.write_text(
        json.dumps(
            {
                "surface": "owner_callable_adapter_receipt_study_latest",
                "executions": [canonical_execution],
                "execution_ledger": [
                    {
                        "surface": "owner_callable_adapter_receipt",
                        "execution_status": "blocked",
                        "action_type": "canonical_paper_inputs_rehydrate_required",
                        "blocked_reason": "canonical_paper_inputs_rehydrate_failed",
                        "next_owner": "write",
                        "owner_callable_surface": "medical_manuscript_blueprint.materialize_medical_manuscript_blueprint",
                        "required_input_surface": "canonical-input.json",
                        "required_output_surface": str(
                            study_root / "paper" / "medical_manuscript_blueprint_source.json"
                        ),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    legacy_path.parent.mkdir(parents=True)
    legacy_path.write_text(
        json.dumps(
            {
                "surface": "default_executor_dispatch_execution_study_latest",
                "executions": [legacy_execution],
                "execution_ledger": [
                    {
                        "surface": "default_executor_dispatch_execution",
                        "execution_status": "blocked",
                        "action_type": "canonical_paper_inputs_rehydrate_required",
                        "blocked_reason": "canonical_paper_inputs_rehydrate_failed",
                        "next_owner": "write",
                        "owner_callable_surface": "legacy.rehydrate",
                        "required_input_surface": "legacy-input.json",
                        "required_output_surface": str(
                            study_root / "paper" / "legacy_medical_manuscript_blueprint_source.json"
                        ),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    admission_candidates = provider_admission.persisted_provider_admission_candidates(
        study_root=study_root,
        status_payload={
            "study_id": "study-1",
            "current_executable_owner_action": {
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "fingerprint-current",
            },
        },
    )
    assert len(admission_candidates) == 1
    assert admission_candidates[0]["work_unit_fingerprint"] == "fingerprint-current"
    assert admission_candidates[0]["execution_ref"] == (
        "artifacts/supervision/consumer/owner_callable_adapter_receipts/latest.json"
    )

    handoff = export_projection._current_provider_handoff_execution(
        study_root=study_root,
        action_type="run_quality_repair_batch",
        work_unit_id="medical_prose_write_repair",
    )
    assert handoff["work_unit_fingerprint"] == "fingerprint-current"
    assert handoff["surface"] == "owner_callable_adapter_receipt"

    rehydrate = recovery_actions._latest_clean_migration_rehydrate_execution(study_root)
    assert (
        rehydrate["owner_callable_surface"]
        == "medical_manuscript_blueprint.materialize_medical_manuscript_blueprint"
    )
    assert rehydrate["surface"] == "owner_callable_adapter_receipt"


def test_dhd_legacy_execution_fallback_is_refs_only_stage_run_intake(tmp_path) -> None:
    diagnostic = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    study_root = tmp_path / "studies" / "study-1"
    legacy_path = study_root / "artifacts" / "supervision" / "consumer" / "default_executor_execution" / "latest.json"
    legacy_path.parent.mkdir(parents=True)
    legacy_path.write_text(
        json.dumps(
            {
                "surface": "default_executor_dispatch_execution_study_latest",
                "executions": [
                    {
                        "surface": "default_executor_dispatch_execution",
                        "study_id": "study-1",
                        "quest_id": "study-1",
                        "execution_status": "handoff_ready",
                        "provider_attempt_or_lease_required": True,
                        "owner_callable_surface": "opl_default_executor.stage_attempt",
                        "owner_route_current": True,
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "fingerprint-legacy",
                        "action_fingerprint": "fingerprint-legacy",
                        "dispatch_path": (
                            "artifacts/supervision/consumer/default_executor_dispatches/"
                            "immutable/run_quality_repair_batch/fingerprint-legacy.json"
                        ),
                        "dispatch_ref": (
                            "artifacts/supervision/consumer/default_executor_dispatches/"
                            "immutable/run_quality_repair_batch/fingerprint-legacy.json"
                        ),
                        "owner_route": {
                            "source_refs": {
                                "work_unit_id": "medical_prose_write_repair",
                                "work_unit_fingerprint": "fingerprint-legacy",
                                "owner_route_currentness_basis": {
                                    "work_unit_id": "medical_prose_write_repair",
                                    "work_unit_fingerprint": "fingerprint-legacy",
                                },
                            }
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    [candidate] = diagnostic._legacy_execution_provider_admission_candidates(
        study_root=study_root,
        status_payload={
            "study_id": "study-1",
            "current_executable_owner_action": {
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "fingerprint-legacy",
            },
        },
    )

    assert candidate["source"] == "legacy_default_executor_refs_only_stage_run_intake"
    assert candidate["status"] == "transition_request_pending"
    assert candidate["dispatch_status"] == "transition_request_pending"
    assert candidate["provider_admission_pending"] is False
    assert candidate["provider_attempt_or_lease_required"] is False
    assert candidate["provider_admission_requires_opl_runtime_result"] is True
    assert candidate["opl_transition_runtime_required"] is True
    assert candidate["legacy_wire_current_reader"] is False
    assert candidate["legacy_wire_can_authorize_provider_admission"] is False
    assert candidate["authority_boundary"]["legacy_wire_can_authorize_provider_admission"] is False
    assert candidate["authority_boundary"]["can_mark_provider_attempt_running"] is False




__all__ = [name for name in globals() if name.startswith("test_")]
