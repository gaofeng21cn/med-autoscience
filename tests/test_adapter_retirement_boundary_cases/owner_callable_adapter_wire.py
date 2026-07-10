from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src" / "med_autoscience"


def test_owner_callable_dispatch_residue_cleanup_surface_is_physically_retired() -> None:
    assert not (
        SRC_ROOT / "controllers" / "owner_callable_dispatch_residue_cleanup.py"
    ).exists()
    assert not (REPO_ROOT / "tests" / "test_owner_callable_dispatch_residue_cleanup.py").exists()

    assert not any((SRC_ROOT / "cli").rglob("*.py"))


def test_open_runtime_surfaces_cannot_use_active_callers_as_retention_reason() -> None:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    open_surfaces = [
        surface
        for surface in inventory["surfaces"]
        if surface["disposition"] != "physically_retired"
    ]

    assert open_surfaces
    for surface in open_surfaces:
        assert surface["mas_runtime_authority"] is False
        assert surface["replacement_ref"].startswith("opl:")
        assert surface["retained_mas_role"] != "none"


def test_owner_callable_receipt_latest_reader_ignores_legacy_latest_wire(tmp_path) -> None:
    candidates = importlib.import_module(
        "med_autoscience.controllers.study_transition_receipt_consumption.owner_callable_candidates"
    )
    study_root = tmp_path / "studies" / "study-1"
    canonical_path = study_root / "artifacts" / "supervision" / "consumer" / "owner_callable_adapter_receipts" / "latest.json"
    legacy_path = study_root / "artifacts" / "supervision" / "consumer" / "owner_callable_adapter_receipt" / "latest.json"
    legacy_path.parent.mkdir(parents=True)
    legacy_path.write_text(
        json.dumps(
            {
                "surface": "owner_callable_dispatch_execution_study_latest",
                "executions": [
                    {
                        "surface": "owner_callable_dispatch_execution",
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

    payload, receipt_ref = candidates.latest_owner_callable_receipt_payload(study_root=study_root)

    assert receipt_ref == "artifacts/supervision/consumer/owner_callable_adapter_receipts/latest.json"
    assert payload["executions"][0]["action_type"] == "canonical_action"
    assert payload["executions"][0]["canonical_surface"] == "owner_callable_adapter_receipt"
    assert payload["projection_authority"] is False
    assert payload["queue_authority"] is False

    canonical_path.unlink()
    payload, receipt_ref = candidates.latest_owner_callable_receipt_payload(study_root=study_root)

    assert payload is None
    assert receipt_ref == "artifacts/supervision/consumer/owner_callable_adapter_receipts/latest.json"
    assert candidates.owner_callable_receipt_candidates(study_root=study_root) == []

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
    }["owner_callable_adapter_receipt_latest_wire_projection"]

    assert surface["disposition"] == "physically_retired"
    assert surface["retained_mas_role"] == "none"
    assert surface["mas_runtime_authority"] is False
    assert surface["tombstone_ref"] == (
        "human_doc:mas-private-surface-retirement#"
        "default_executor_execution_latest_wire_projection"
    )

    audit = retirement.audit_runtime_surface_retirement_inventory(inventory)
    assert "owner_callable_adapter_receipt_latest_wire_projection" in audit[
        "retired_surface_ids"
    ]
    assert audit["completion_claim_allowed"] is False
    assert audit["live_runtime_readiness_claim_allowed"] is False

    bad_inventory = json.loads(json.dumps(inventory))
    bad_surface = {
        item["surface_id"]: item for item in bad_inventory["surfaces"]
    }["owner_callable_adapter_receipt_latest_wire_projection"]
    bad_surface["tombstone_ref"] = None

    violations = retirement.validate_runtime_surface_retirement_inventory(bad_inventory)

    assert {
        (
            "owner_callable_adapter_receipt_latest_wire_projection",
            "retired_surface_missing_tombstone",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in violations}


def test_domain_owner_dispatch_execution_latest_payload_ignores_legacy_opt_in(
    tmp_path,
) -> None:
    execution_io = importlib.import_module(
        "med_autoscience.controllers.stage_outcome_authority.execution_io"
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
        / "owner_callable_adapter_receipt"
        / "latest.json"
    )
    legacy_path.parent.mkdir(parents=True)
    legacy_path.write_text(
        json.dumps(
            {
                "surface": "owner_callable_dispatch_execution_study_latest",
                "executions": [
                    {
                        "surface": "owner_callable_dispatch_execution",
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


def test_current_owner_callable_readers_do_not_consume_legacy_latest_wire(tmp_path) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.provider_admission.provider_admission"
    )
    export_projection = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff.export_study_projection"
    )
    recovery_actions = importlib.import_module(
        "med_autoscience.controllers.paper_mission_owner_surface.recovery_actions"
    )
    study_root = tmp_path / "studies" / "study-1"
    legacy_path = study_root / "artifacts" / "supervision" / "consumer" / "owner_callable_adapter_receipt" / "latest.json"
    legacy_execution = {
        "surface": "owner_callable_dispatch_execution",
        "study_id": "study-1",
        "quest_id": "study-1",
        "execution_status": "handoff_ready",
        "provider_attempt_or_lease_required": True,
        "owner_callable_surface": "opl_owner_callable_adapter.stage_attempt",
        "owner_route_current": True,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "fingerprint-legacy",
        "action_fingerprint": "fingerprint-legacy",
        "dispatch_path": "artifacts/supervision/consumer/owner_callable_adapters/immutable/run_quality_repair_batch/fingerprint-legacy.json",
        "dispatch_ref": "artifacts/supervision/consumer/owner_callable_adapters/immutable/run_quality_repair_batch/fingerprint-legacy.json",
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
                "surface": "owner_callable_dispatch_execution_study_latest",
                "executions": [legacy_execution],
                "execution_ledger": [
                    {
                        "surface": "owner_callable_dispatch_execution",
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
        "med_autoscience.controllers.provider_admission.provider_admission"
    )
    export_projection = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff.export_study_projection"
    )
    recovery_actions = importlib.import_module(
        "med_autoscience.controllers.paper_mission_owner_surface.recovery_actions"
    )
    study_root = tmp_path / "studies" / "study-1"
    canonical_path = study_root / "artifacts" / "supervision" / "consumer" / "owner_callable_adapter_receipts" / "latest.json"
    legacy_path = study_root / "artifacts" / "supervision" / "consumer" / "owner_callable_adapter_receipt" / "latest.json"
    canonical_execution = {
        "surface": "owner_callable_adapter_receipt",
        "study_id": "study-1",
        "quest_id": "study-1",
        "execution_status": "handoff_ready",
        "provider_attempt_or_lease_required": True,
        "owner_callable_surface": "opl_owner_callable_adapter.stage_attempt",
        "owner_route_current": True,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "fingerprint-current",
        "action_fingerprint": "fingerprint-current",
        "dispatch_path": "artifacts/supervision/consumer/owner_callable_adapters/immutable/run_quality_repair_batch/fingerprint-current.json",
        "dispatch_ref": "artifacts/supervision/consumer/owner_callable_adapters/immutable/run_quality_repair_batch/fingerprint-current.json",
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
        "surface": "owner_callable_dispatch_execution",
        "work_unit_fingerprint": "fingerprint-legacy",
        "action_fingerprint": "fingerprint-legacy",
        "dispatch_path": "artifacts/supervision/consumer/owner_callable_adapters/immutable/run_quality_repair_batch/fingerprint-legacy.json",
        "dispatch_ref": "artifacts/supervision/consumer/owner_callable_adapters/immutable/run_quality_repair_batch/fingerprint-legacy.json",
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
                "surface": "owner_callable_dispatch_execution_study_latest",
                "executions": [legacy_execution],
                "execution_ledger": [
                    {
                        "surface": "owner_callable_dispatch_execution",
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


__all__ = [name for name in globals() if name.startswith("test_")]
