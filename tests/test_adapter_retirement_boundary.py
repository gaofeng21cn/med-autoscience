from __future__ import annotations

import json
import importlib
from pathlib import Path

from med_autoscience.controllers.default_executor_action_policy import (
    SUPPORTED_ACTION_TYPES,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src" / "med_autoscience"
ADAPTER_ROOT = SRC_ROOT / "adapters" / "deepscientist"
RUNTIME_TRANSPORT_ROOT = SRC_ROOT / "runtime_transport"


def test_production_code_does_not_import_deepscientist_adapters() -> None:
    violations: list[str] = []
    for path in sorted(SRC_ROOT.rglob("*.py")):
        if path.is_relative_to(ADAPTER_ROOT):
            continue
        text = path.read_text(encoding="utf-8")
        if "med_autoscience.adapters.deepscientist" not in text and "adapters.deepscientist" not in text:
            continue
        violations.append(str(path.relative_to(REPO_ROOT)))

    assert violations == []


def test_legacy_deepscientist_adapter_modules_are_removed() -> None:
    assert not (ADAPTER_ROOT / "__init__.py").exists()
    assert not (ADAPTER_ROOT / "daemon_api.py").exists()
    assert not (ADAPTER_ROOT / "mailbox.py").exists()
    assert not (ADAPTER_ROOT / "runtime.py").exists()
    assert not (ADAPTER_ROOT / "paper_bundle.py").exists()


def test_legacy_manual_finishing_projection_field_is_not_resurrected() -> None:
    violations: list[str] = []
    for path in sorted(SRC_ROOT.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if "legacy_current_stage" in text:
            violations.append(str(path.relative_to(REPO_ROOT)))

    assert violations == []


def test_mas_private_runtime_transport_modules_are_physically_retired() -> None:
    assert not RUNTIME_TRANSPORT_ROOT.exists()


def test_production_code_does_not_import_retired_mas_runtime_transport_modules() -> None:
    forbidden_tokens = (
        "med_autoscience.runtime_transport.mas_runtime_core",
        "from med_autoscience.runtime_transport import mas_runtime_core",
        "from med_autoscience.runtime_transport import mas_runtime_core_",
        "med_autoscience.runtime_transport import mas_runtime_core",
    )
    violations: list[str] = []
    for path in sorted(SRC_ROOT.rglob("*.py")):
        if path.is_relative_to(RUNTIME_TRANSPORT_ROOT):
            continue
        text = path.read_text(encoding="utf-8")
        if any(token in text for token in forbidden_tokens):
            violations.append(str(path.relative_to(REPO_ROOT)))

    assert violations == []


def test_retired_runtime_supervisor_dispatch_executor_test_helper_is_removed() -> None:
    assert not (REPO_ROOT / "tests" / "runtime_supervisor_dispatch_executor_helpers.py").exists()


def test_runtime_like_surfaces_have_machine_readable_opl_migration_inventory() -> None:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))

    assert inventory["surface_kind"] == "mas_runtime_surface_retirement_inventory"
    assert inventory["version"] == "mas-runtime-surface-retirement-inventory.v1"
    assert inventory["authority_boundary"] == {
        "opl_owns": [
            "queue",
            "attempt",
            "retry",
            "dead_letter",
            "provider_liveness",
            "generic_stage_state",
        ],
        "mas_owns": [
            "domain_truth",
            "ai_reviewer",
            "publication_gate",
            "artifact_authority",
            "owner_receipt",
            "typed_blocker",
        ],
    }
    assert inventory["compatibility_alias_policy"] == {
        "new_alias_allowed": False,
        "active_adapter_can_claim_mas_owner": False,
    }

    surfaces = {item["surface_id"]: item for item in inventory["surfaces"]}
    assert set(surfaces) >= {
        "runtime_transport_core_bridge",
        "runtime_turn_runner_closeout_adapter",
        "worker_lease_residency_projection",
        "domain_authority_refs_index",
        "default_executor_dispatch_request",
        "domain_action_request_materializer_local_carrier_persistence_api",
        "owner_callable_adapter_legacy_dispatch_projection_alias",
        "domain_action_request_materializer_current_default_executor_dispatches_api",
        "domain_action_request_materializer_owner_callable_adapter_projection",
        "default_executor_execution_latest_wire_projection",
        "domain_owner_action_dispatch",
        "domain_health_diagnostic_obligation_actuator",
    }
    for surface in surfaces.values():
        assert surface["generic_runtime_owner"] == "one-person-lab"
        assert surface["mas_owner_claim_allowed"] is False
        assert surface["compatibility_alias_allowed"] is False
        if surface["surface_id"] in {
            "runtime_transport_core_bridge",
            "runtime_turn_runner_closeout_adapter",
            "worker_lease_residency_projection",
            "domain_action_request_materializer_local_carrier_persistence_api",
            "owner_callable_adapter_legacy_dispatch_projection_alias",
            "domain_action_request_materializer_current_default_executor_dispatches_api",
        }:
            assert surface["active_caller_migrated"] is True
            assert surface["current_disposition"] == "physically_retired"
        assert "mas_owned_generic_runtime" in surface["forbidden_claims"]

    carrier_persistence = surfaces["domain_action_request_materializer_local_carrier_persistence_api"]
    assert carrier_persistence["retained_mas_role"] == "none_physically_retired_no_alias"
    assert carrier_persistence["replacement_surface"] == (
        "domain_progress_transition_requests plus OPL DomainProgressTransitionRuntime durable carrier"
    )
    assert set(carrier_persistence["retired_symbols"]) == {
        "persist_default_executor_dispatches",
        "persist_request_packets",
        "persist_consumer_payload",
        "request_packet_for_persistence",
        "medical_paper_readiness_packet_for_persistence",
        "source_workflow_ref_for_ai_reviewer_request",
    }
    assert "mas_local_dispatch_carrier_persistence" in carrier_persistence["forbidden_claims"]
    assert "mas_local_request_packet_persistence" in carrier_persistence["forbidden_claims"]

    default_dispatch = surfaces["default_executor_dispatch_request"]
    assert default_dispatch["legacy_carrier_fallback_only"] is True
    assert (
        default_dispatch["priority_boundary"]
        == "current_control_transition_request_precedes_legacy_dispatch_carrier"
    )
    assert default_dispatch["projection_counting_boundary"] == {
        "opl_live_readback_candidates_count_as": "provider_admission_pending",
        "request_only_candidates_count_as": "transition_request_pending",
        "opl_log_derived_readback_candidates_count_as": "deprecated_diagnostic_only",
        "mutually_exclusive_pending_counts": True,
        "forbidden_double_count": (
            "same_identity_transition_request_pending_and_provider_admission_pending"
        ),
    }
    assert default_dispatch["arbiter_authority_boundary"] == {
        "provider_admission_readback_requires_opl_live_readback": True,
        "event_or_outbox_fragment_is_provider_admission_authority": False,
        "request_without_live_readback_effect": "transition_request_pending_non_advancing_apply_required",
        "missing_live_readback_no_progress_signal": "transition_request_waits_for_opl_runtime",
        "anti_loop_classification": "non_advancing_apply_required",
        "mas_can_authorize_provider_admission": False,
        "mas_can_create_opl_outbox_event_or_stage_run": False,
    }

    legacy_alias = surfaces["owner_callable_adapter_legacy_dispatch_projection_alias"]
    assert legacy_alias["retained_mas_role"] == "none_physically_retired_no_alias"
    assert legacy_alias["replacement_surface"] == (
        "explicit domain_progress_transition_requests projection plus OPL DomainProgressTransitionRuntime readback"
    )
    assert legacy_alias["retired_symbols"] == [
        "default_executor_dispatches owner_callable_adapters fallback alias"
    ]
    assert "legacy_default_executor_dispatches_as_owner_callable_adapters" in legacy_alias["forbidden_claims"]

    current_default_preview = surfaces["domain_action_request_materializer_current_default_executor_dispatches_api"]
    assert current_default_preview["retained_mas_role"] == "none_physically_retired_no_alias"
    assert current_default_preview["replacement_surface"] == (
        "current_owner_callable_adapters projection plus OPL DomainProgressTransitionRuntime readback"
    )
    assert set(current_default_preview["retired_symbols"]) == {
        "current_default_executor_dispatches",
        "domain_action_request_materializer_parts.current_default_executor_dispatches",
    }
    assert "legacy_current_default_executor_dispatches_preview_api" in current_default_preview["forbidden_claims"]

    owner_callable_projection = surfaces["domain_action_request_materializer_owner_callable_adapter_projection"]
    assert owner_callable_projection["active_caller_migrated"] is True
    assert (
        owner_callable_projection["current_disposition"]
        == "direct_readback_migrated_legacy_diagnostic_projection_only"
    )
    assert owner_callable_projection["retained_mas_role"] == "migration_diagnostic_projection_only"
    assert owner_callable_projection["canonical_surface"] == "domain_progress_transition_requests"
    assert owner_callable_projection["retention_reason"] == (
        "temporary migration diagnostic projection only; active direct readback now suppresses top-level "
        "owner_callable_adapters and exposes canonical domain_progress_transition_requests while OPL live "
        "readback remains the physical retirement gate"
    )
    assert owner_callable_projection["retirement_gate"] == {
        "active_caller_alone_retains_surface": False,
        "completion_claim_requires_live_owner_or_opl_readback": True,
        "no_active_caller_required_before_physical_delete": True,
        "no_forbidden_write_proof_required": True,
        "replacement_parity_required": True,
        "tombstone_or_provenance_required": True,
    }
    assert owner_callable_projection["legacy_projection_boundary"] == {
        "canonical_transition_request_surface": "domain_progress_transition_requests",
        "owner_callable_adapter_counts_authority": False,
        "owner_callable_adapter_item_can_create_success_outcome": False,
        "owner_callable_adapter_item_diagnostic_only": True,
        "owner_callable_adapter_item_readiness_authority": False,
        "owner_callable_adapter_list_can_create_success_outcome": False,
        "owner_callable_adapter_list_diagnostic_only": True,
        "owner_callable_adapter_readiness_authority": False,
    }
    assert "ready_owner_callable_adapter_count_as_provider_admission" in owner_callable_projection[
        "forbidden_claims"
    ]
    assert "owner_callable_adapters_as_success_outcome" in owner_callable_projection[
        "forbidden_claims"
    ]
    assert "legacy_caller_exists" not in owner_callable_projection["retention_reason"]
    assert owner_callable_projection["verified_by"] == [
        (
            "tests/test_domain_action_request_materializer.py::"
            "test_materialize_domain_action_requests_only_writes_current_owner_dispatch_for_route_epoch"
        ),
        (
            "tests/domain_action_request_materializer_cases/test_paper_recovery_owner_callable.py::"
            "test_current_default_dispatch_for_execution_marks_paper_recovery_callable_ready"
        ),
    ]

    execution_latest = surfaces["default_executor_execution_latest_wire_projection"]
    assert execution_latest["active_caller_migrated"] is True
    assert (
        execution_latest["current_disposition"]
        == "canonical_writer_and_readers_migrated_legacy_wire_provenance_fallback"
    )
    assert execution_latest["retained_mas_role"] == "owner_callable_receipt_projection_and_domain_authority_ref"
    assert execution_latest["canonical_surface"] == "owner_callable_adapter_receipt_study_latest"
    assert execution_latest["canonical_wire_path"] == (
        "artifacts/supervision/consumer/owner_callable_adapter_receipts/latest.json"
    )
    assert execution_latest["legacy_wire_surface"] == "default_executor_dispatch_execution_study_latest"
    assert execution_latest["legacy_wire_path"] == "artifacts/supervision/consumer/default_executor_execution/latest.json"
    assert execution_latest["legacy_wire_readers_tail_open"] == []
    assert set(execution_latest["canonical_first_readers"]) == {
        "domain_health_diagnostic_parts.provider_admission.persisted_provider_admission_candidates",
        "owner_route_handoff_parts.export_study_projection._current_provider_handoff_execution",
        "owner_route_reconcile_parts.recovery_actions._latest_clean_migration_rehydrate_execution",
    }
    assert "mas_local_execution_ledger_authority" in execution_latest["forbidden_claims"]

    owner_dispatch = surfaces["domain_owner_action_dispatch"]
    assert owner_dispatch["active_caller_migrated"] is True
    assert owner_dispatch["current_disposition"] == "opl_authorized_owner_callable_adapter"
    assert (
        owner_dispatch["retained_mas_role"]
        == "owner_callable_adapter_policy_boundary_and_typed_blocker_projection"
    )
    assert owner_dispatch["retention_reason"] == (
        "temporary owner callable adapter until OPL DomainProgressTransitionRuntime "
        "provides live authorization and callable execution readback for every active caller"
    )
    assert owner_dispatch["retirement_gate"] == {
        "active_caller_alone_retains_surface": False,
        "completion_claim_requires_live_owner_or_opl_readback": True,
        "live_every_active_caller_soak_required": True,
        "no_active_caller_required_before_physical_delete": True,
        "no_forbidden_write_proof_required": True,
        "replacement_parity_required": True,
        "tombstone_or_provenance_required": True,
    }
    assert owner_dispatch["execution_authorization_boundary"] == {
        "execution_authorization_sources": [
            "trusted_opl_execution_authorization",
            "exact_provider_hosted_stage_attempt",
            "active_opl_provider_attempt_or_lease",
            "bound_opl_domain_progress_transition_runtime_readback",
        ],
        "closeout_binding_authorizes_execution": False,
        "repo_level_authorization_coverage_complete": True,
        "live_every_active_caller_soak_required": True,
        "missing_authorization_outcome": "opl_execution_authorization_required_typed_blocker",
        "provider_attempt_or_lease_required_when_blocked": False,
    }
    assert owner_dispatch["execution_authorization_coverage"] == {
        "coverage_status": "repo_fail_closed_all_supported_actions_live_readback_tail_open",
        "supported_action_types_ref": (
            "src/med_autoscience/controllers/default_executor_action_policy.py#SUPPORTED_ACTION_TYPES"
        ),
        "repo_fail_closed_test_ref": (
            "tests/test_domain_owner_action_dispatch_contract.py::"
            "test_transition_request_projection_requires_opl_execution_authorization_for_every_supported_action"
        ),
        "request_projection_without_opl_proof_outcome": "opl_execution_authorization_required",
        "repo_covered_action_families": sorted(SUPPORTED_ACTION_TYPES),
        "live_readback_required_before_retirement": True,
        "live_tail": "live_every_active_caller_soak_or_no_active_caller_proof",
    }
    assert "mas_local_dispatch_authority" in owner_dispatch["forbidden_claims"]
    assert "closeout_binding_as_execution_authorization" in owner_dispatch["forbidden_claims"]
    assert "legacy_caller_exists" not in owner_dispatch["retention_reason"]

    runtime_health = surfaces["runtime_health_kernel"]
    assert runtime_health["current_disposition"] == "read_only_diagnostic_publisher"
    assert runtime_health["active_caller_migrated"] is True
    assert runtime_health["local_event_log_append_from_status_payload"] is False
    assert runtime_health["mas_local_event_append_api_retired"] is True
    assert runtime_health["historical_event_log_role"] == (
        "legacy_fixture_and_explicit_archive_import_provenance_input_only"
    )
    assert runtime_health["retired_code_symbols"] == [
        "runtime_health_kernel.append_runtime_health_event",
        "runtime_health_kernel_parts.event_log.append_runtime_health_event",
    ]
    assert "tests/test_adapter_retirement_boundary.py" in runtime_health["verified_by"]
    assert "mas_owned_attempt_ledger" in runtime_health["forbidden_claims"]

    obligation_actuator = surfaces["domain_health_diagnostic_obligation_actuator"]
    assert obligation_actuator["current_disposition"] == "opl_recovery_obligation_readback_consumer"
    assert obligation_actuator["retained_mas_role"] == (
        "consume_only_obligation_outcome_projection_and_fail_closed_typed_blocker"
    )
    assert obligation_actuator["obligation_readback_boundary"] == {
        "success_outcome_source_families": [
            "opl_runtime_readback",
            "mas_owner_answer_readback",
            "mas_domain_authority_readback",
        ],
        "request_projection_is_success_outcome": False,
        "supervisor_disallowed_outcome_is_success": False,
    }
    assert "mas_owned_recovery_obligation_store" in obligation_actuator["forbidden_claims"]
    assert "mas_owned_supervisor_decision_engine" in obligation_actuator["forbidden_claims"]
    assert "mas_policy_request_projection_as_success_outcome" in obligation_actuator["forbidden_claims"]


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


def test_owner_callable_receipt_latest_reader_prefers_canonical_and_normalizes_legacy(tmp_path) -> None:
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

    assert receipt_ref == "artifacts/supervision/consumer/default_executor_execution/latest.json"
    assert payload["executions"][0]["action_type"] == "legacy_action"
    assert payload["executions"][0]["surface"] == "owner_callable_adapter_receipt"
    assert payload["executions"][0]["legacy_wire_surface"] == "default_executor_dispatch_execution"
    assert payload["execution_ledger_authority"] is False
    assert payload["attempt_lifecycle_authority"] is False


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


def test_materializer_local_carrier_persistence_api_is_physically_retired() -> None:
    persistence = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.persistence"
    )

    for symbol in (
        "persist_default_executor_dispatches",
        "persist_request_packets",
        "persist_consumer_payload",
        "request_packet_for_persistence",
        "medical_paper_readiness_packet_for_persistence",
        "source_workflow_ref_for_ai_reviewer_request",
    ):
        assert not hasattr(persistence, symbol), symbol

    assert hasattr(persistence, "read_json_object")
    assert hasattr(persistence, "write_json")


def test_owner_callable_projection_does_not_accept_legacy_dispatch_alias() -> None:
    projection = importlib.import_module("med_autoscience.controllers.owner_callable_adapter_projection")

    assert projection.owner_callable_adapters(
        {
            "default_executor_dispatches": [
                {"dispatch_status": "ready", "action_type": "legacy_dispatch"},
            ],
        }
    ) == []
    assert projection.adapter_count(
        {
            "default_executor_dispatches": [
                {"dispatch_status": "ready", "action_type": "legacy_dispatch"},
            ],
        }
    ) == 0
    assert projection.adapter_status_count(
        {
            "default_executor_dispatches": [
                {"dispatch_status": "ready", "action_type": "legacy_dispatch"},
            ],
        },
        "ready",
    ) == 0
    assert projection.domain_progress_transition_requests(
        {
            "default_executor_dispatches": [
                {
                    "dispatch_status": "ready",
                    "action_type": "legacy_dispatch",
                    "opl_domain_progress_transition_request": {
                        "surface_kind": "mas_domain_progress_transition_request",
                    },
                },
            ],
        }
    ) == []
    assert projection.transition_request_count(
        {
            "default_executor_dispatches": [
                {
                    "dispatch_status": "transition_request_pending",
                    "action_type": "legacy_dispatch",
                    "opl_domain_progress_transition_request": {
                        "surface_kind": "mas_domain_progress_transition_request",
                    },
                },
            ],
        }
    ) == 0


def test_transition_request_counts_are_canonical_not_legacy_adapter_counts() -> None:
    projection = importlib.import_module("med_autoscience.controllers.owner_callable_adapter_projection")

    payload = {
        "owner_callable_adapter_count": 99,
        "ready_owner_callable_adapter_count": 88,
        "owner_callable_adapters": [
            {"dispatch_status": "ready", "action_type": "legacy_ready"},
        ],
        "domain_progress_transition_requests": [
            {
                "study_id": "study-1",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "repair-work",
                "work_unit_fingerprint": "fingerprint-1",
                "dispatch_status": "transition_request_pending",
            },
            {
                "study_id": "study-1",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "gate-work",
                "work_unit_fingerprint": "fingerprint-2",
                "dispatch_status": "blocked",
            },
        ],
    }

    assert projection.legacy_owner_callable_adapter_count(payload) == 99
    assert projection.legacy_owner_callable_adapter_status_count(payload, "ready") == 88
    assert projection.adapter_count(payload) == projection.legacy_owner_callable_adapter_count(payload)
    assert projection.adapter_status_count(
        payload,
        "ready",
    ) == projection.legacy_owner_callable_adapter_status_count(payload, "ready")
    assert projection.transition_request_count(payload) == 2
    assert projection.transition_request_status_count(payload, "transition_request_pending") == 1
    assert projection.transition_request_status_count(payload, "blocked") == 1
    diagnostics = projection.legacy_owner_callable_adapter_diagnostics(payload)
    assert diagnostics["surface"] == "legacy_owner_callable_adapter_diagnostics"
    assert diagnostics["canonical_transition_request_surface"] == "domain_progress_transition_requests"
    assert diagnostics["diagnostic_only"] is True
    assert diagnostics["counts_authority"] is False
    assert diagnostics["readiness_authority"] is False
    assert diagnostics["can_create_success_outcome"] is False
    assert diagnostics["body_authority"] is False
    assert diagnostics["body_projection"] is False
    assert diagnostics["legacy_payload_scope"] == "identity_refs_only"
    assert diagnostics["legacy_dispatch_count"] == 1
    assert diagnostics["legacy_ready_count"] == 1
    assert diagnostics["legacy_blocked_count"] == 0
    assert diagnostics["legacy_transition_request_pending_count"] == 0
    assert diagnostics["legacy_dispatches"] == [
        {
            "diagnostic_ref_only": True,
            "payload_body_omitted": True,
            "action_type": "legacy_ready",
            "dispatch_status": "ready",
        }
    ]
    assert diagnostics["legacy_dispatch_refs"] == diagnostics["legacy_dispatches"]
    assert diagnostics["legacy_dispatch_body_omitted"] is True
    assert "source_action" not in diagnostics["legacy_dispatches"][0]
    assert "owner_route" not in diagnostics["legacy_dispatches"][0]
    assert "prompt_contract" not in diagnostics["legacy_dispatches"][0]


def test_owner_callable_projection_requires_canonical_transition_request_surface() -> None:
    projection = importlib.import_module("med_autoscience.controllers.owner_callable_adapter_projection")

    legacy_payload = {
        "owner_callable_adapters": [
            {
                "study_id": "study-1",
                "quest_id": "quest-1",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "repair-work",
                "work_unit_fingerprint": "fingerprint-1",
                "dispatch_status": "transition_request_pending",
                "target_runtime_owner": "one-person-lab",
                "refs": {
                    "dispatch_path": (
                        "artifacts/supervision/consumer/default_executor_dispatches/"
                        "run_quality_repair_batch.json"
                    )
                },
                "opl_domain_progress_transition_request": {
                    "surface_kind": "mas_domain_progress_transition_request",
                    "study_id": "study-1",
                    "quest_id": "quest-1",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "repair-work",
                    "work_unit_fingerprint": "fingerprint-1",
                },
            }
        ]
    }

    assert projection.domain_progress_transition_requests(legacy_payload) == []
    assert projection.with_owner_callable_adapter_projection(legacy_payload)[
        "domain_progress_transition_request_count"
    ] == 0
    legacy_projected = projection.with_owner_callable_adapter_projection(legacy_payload)
    assert "owner_callable_adapter_list_diagnostic_only" not in legacy_projected
    assert "owner_callable_adapter_count" not in legacy_projected
    assert "owner_callable_adapters" in legacy_payload
    assert "owner_callable_adapters" not in legacy_projected
    assert legacy_projected["legacy_owner_callable_adapter_diagnostics"]["diagnostic_only"] is True
    assert legacy_projected["legacy_owner_callable_adapter_diagnostics"]["legacy_dispatch_count"] == 1
    assert legacy_projected["canonical_transition_request_surface"] == (
        "domain_progress_transition_requests"
    )

    canonical_payload = {
        "domain_progress_transition_requests": [
            {
                "study_id": "study-1",
                "quest_id": "quest-1",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "repair-work",
                "work_unit_fingerprint": "fingerprint-1",
                "dispatch_status": "transition_request_pending",
                "target_runtime_owner": "one-person-lab",
                "opl_domain_progress_transition_request": {
                    "surface_kind": "mas_domain_progress_transition_request",
                    "study_id": "study-1",
                    "quest_id": "quest-1",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "repair-work",
                    "work_unit_fingerprint": "fingerprint-1",
                },
            }
        ]
    }

    requests = projection.domain_progress_transition_requests(canonical_payload)

    assert len(requests) == 1
    assert requests[0]["surface"] == "mas_domain_progress_transition_request_projection"
    assert requests[0]["study_id"] == "study-1"
    assert requests[0]["action_type"] == "run_quality_repair_batch"
    assert requests[0]["work_unit_fingerprint"] == "fingerprint-1"
    assert requests[0]["mas_dispatch_authority"] is False
    assert requests[0]["mas_creates_owner_callable_carrier"] is False
    assert requests[0]["mas_creates_opl_outbox"] is False
    assert requests[0]["provider_admission_pending"] is False
    assert requests[0]["provider_admission_requires_opl_runtime_result"] is True
    projected = projection.with_owner_callable_adapter_projection(canonical_payload)
    assert projected["domain_progress_transition_request_count"] == 1
    assert "owner_callable_adapter_list_diagnostic_only" not in projected
    assert "owner_callable_adapter_count" not in projected
    assert "owner_callable_adapters" not in projected


def test_materializer_canonical_projection_preserves_strong_identity_without_legacy_body() -> None:
    transition_request_projection = importlib.import_module(
        "med_autoscience.controllers.domain_action_request_materializer_parts.transition_request_projection"
    )
    projection = importlib.import_module("med_autoscience.controllers.owner_callable_adapter_projection")

    dispatch = {
        "study_id": "study-1",
        "quest_id": "quest-1",
        "action_type": "run_quality_repair_batch",
        "dispatch_status": "transition_request_pending",
        "refs": {
            "dispatch_path": "studies/study-1/artifacts/supervision/consumer/default_executor_dispatches/run_quality_repair_batch.json",
            "route_identity_key": "route::from-refs",
            "attempt_idempotency_key": "attempt::from-refs",
        },
        "owner_route": {
            "next_owner": "write",
            "work_unit_fingerprint": "fingerprint-from-route",
            "route_identity_key": "route::from-owner-route",
            "attempt_idempotency_key": "attempt::from-owner-route",
            "source_refs": {
                "work_unit_id": "work-unit-from-route-refs",
                "work_unit_fingerprint": "fingerprint-from-route-refs",
                "owner_route_currentness_basis": {
                    "truth_epoch": "truth-1",
                    "runtime_health_epoch": "runtime-1",
                    "work_unit_id": "work-unit-from-currentness",
                    "work_unit_fingerprint": "fingerprint-from-currentness",
                    "route_identity_key": "route::from-currentness",
                    "attempt_idempotency_key": "attempt::from-currentness",
                },
            },
        },
        "prompt_contract": {
            "study_id": "study-1",
            "quest_id": "quest-1",
            "action_type": "run_quality_repair_batch",
            "next_executable_owner": "write",
            "owner_route_currentness_basis": {
                "truth_epoch": "truth-1",
                "runtime_health_epoch": "runtime-1",
            },
            "opl_domain_progress_transition_request": {
                "surface_kind": "mas_domain_progress_transition_request",
                "target_runtime_owner": "one-person-lab",
                "study_id": "study-1",
                "quest_id": "quest-1",
                "action_type": "run_quality_repair_batch",
                "route_identity_key": "route::from-request",
                "attempt_idempotency_key": "attempt::from-request",
            },
        },
        "source_action": {
            "work_unit_id": "work-unit-from-source-action",
            "work_unit_fingerprint": "fingerprint-from-source-action",
        },
    }

    requests = transition_request_projection.domain_progress_transition_request_projection([dispatch])

    assert len(requests) == 1
    request = requests[0]
    assert request["surface"] == "mas_domain_progress_transition_request_projection"
    assert request["route_identity_key"] == "route::from-request"
    assert request["attempt_idempotency_key"] == "attempt::from-request"
    assert request["work_unit_id"] == "work-unit-from-source-action"
    assert request["work_unit_fingerprint"] == "fingerprint-from-source-action"
    assert request["currentness_basis"] == {
        "truth_epoch": "truth-1",
        "runtime_health_epoch": "runtime-1",
        "work_unit_id": "work-unit-from-source-action",
        "work_unit_fingerprint": "fingerprint-from-source-action",
        "route_identity_key": "route::from-currentness",
        "attempt_idempotency_key": "attempt::from-currentness",
    }
    assert request["provider_admission_pending"] is False
    assert request["provider_admission_requires_opl_runtime_result"] is True
    assert request["mas_creates_opl_outbox"] is False
    assert request["mas_creates_opl_event"] is False
    assert request["mas_creates_opl_stage_run"] is False

    diagnostics = projection.legacy_owner_callable_adapter_diagnostics(
        {"owner_callable_adapters": [dispatch]}
    )
    assert diagnostics["legacy_dispatch_body_omitted"] is True
    assert diagnostics["legacy_dispatches"] == diagnostics["legacy_dispatch_refs"]
    legacy_ref = diagnostics["legacy_dispatches"][0]
    assert legacy_ref["diagnostic_ref_only"] is True
    assert legacy_ref["payload_body_omitted"] is True
    assert "owner_route" not in legacy_ref
    assert "prompt_contract" not in legacy_ref
    assert "source_action" not in legacy_ref
    assert "opl_domain_progress_transition_request" not in legacy_ref


def test_dhd_same_tick_admission_consumes_only_canonical_transition_requests(tmp_path: Path) -> None:
    report_module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report"
    )
    source = (
        REPO_ROOT
        / "src"
        / "med_autoscience"
        / "controllers"
        / "domain_health_diagnostic_parts"
        / "provider_admission_report.py"
    ).read_text(encoding="utf-8")

    assert "import owner_callable_adapters" not in source
    assert "owner_callable_adapters(materialize_result)" not in source

    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    dispatch = {
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        "dispatch_status": "transition_request_pending",
        "opl_domain_progress_transition_request": {
            "surface_kind": "mas_domain_progress_transition_request",
            "target_runtime_owner": "one-person-lab",
        },
    }

    result = report_module.materialize_report_provider_admission_current_control_state(
        profile=profile,
        report={
            "domain_action_request_materialization_preview": {
                "owner_callable_adapters": [dispatch],
            },
            "current_execution_evidence": {
                "progress_currentness": {
                    study_id: {
                        "current_executable_owner_action": {
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": "medical_prose_write_repair",
                            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                        },
                    },
                },
            },
            "managed_study_actions": [{"study_id": study_id}],
        },
        apply=False,
        generated_at="2026-06-18T00:00:00+00:00",
    )

    assert result is None or result["transition_request_pending_count"] == 0
    assert result is None or result["provider_admission_pending_count"] == 0


def test_dhd_same_tick_blocker_summary_ignores_legacy_adapter_list() -> None:
    same_tick = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.developer_supervisor_same_tick"
    )
    legacy_blocked = {
        "study_id": "study-1",
        "action_type": "run_gate_clearing_batch",
        "dispatch_status": "blocked",
        "blocked_reason": "legacy_adapter_blocker_should_not_drive_summary",
    }
    canonical_blocked = {
        "study_id": "study-1",
        "action_type": "run_quality_repair_batch",
        "dispatch_status": "blocked",
        "blocked_reason": "canonical_transition_request_blocked",
    }

    diagnostic = same_tick._same_tick_terminal_diagnostic(
        stop_reason="typed_blocker_or_dispatch_blocker_observed",
        iterations=[
            {
                "materialize": {
                    "owner_callable_adapters": [legacy_blocked],
                    "domain_progress_transition_requests": [canonical_blocked],
                },
                "dispatch": {"executions": []},
                "progress_first_delta": {
                    "blocked_owner_callable_adapter_count": 1,
                    "legacy_blocked_owner_callable_adapter_count": 1,
                    "dispatch_blocked_count": 0,
                },
            }
        ],
    )

    summary = diagnostic["dispatch_blocker_summary"]
    assert summary["blocked_owner_callable_adapter_count"] == 1
    assert summary["legacy_blocked_owner_callable_adapter_count"] == 1
    assert summary["blocked_reasons"] == ["canonical_transition_request_blocked"]
    assert summary["blocked_actions"] == ["run_quality_repair_batch"]
    assert "legacy_adapter_blocker_should_not_drive_summary" not in summary["blocked_reasons"]


def test_dhd_dry_run_preview_does_not_consume_legacy_adapter_list_as_carrier() -> None:
    source = (
        REPO_ROOT
        / "src"
        / "med_autoscience"
        / "controllers"
        / "domain_health_diagnostic_parts"
        / "runtime_dry_run_previews.py"
    ).read_text(encoding="utf-8")

    assert "import owner_callable_adapters" not in source
    assert "owner_callable_adapters(preview)" not in source
    assert "domain_progress_transition_requests(preview)" in source


def test_paper_recovery_export_consumes_only_canonical_transition_request_preview(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.owner_route_handoff_parts.paper_recovery_default_executor_tasks"
    )
    materializer = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    dispatch = {
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        "dispatch_status": "transition_request_pending",
        "next_executable_owner": "write",
        "opl_domain_progress_transition_request": {
            "surface_kind": "mas_domain_progress_transition_request",
            "target_runtime_owner": "one-person-lab",
        },
    }
    current_progress = {
        "study_id": study_id,
        "quest_id": study_id,
        "paper_recovery_state": {
            "phase": "owner_action_ready",
            "next_safe_action": {
                "kind": "run_mas_owner_callable",
            },
            "supervisor_decision": {
                "decision": "materialize_recovery_action",
            },
        },
    }

    monkeypatch.setattr(
        materializer,
        "current_owner_callable_adapters",
        lambda **_: {"owner_callable_adapters": [dict(dispatch)]},
    )

    owner_callable_only_tasks = module.paper_recovery_default_executor_dispatch_tasks(
        current_progress=current_progress,
        profile=profile,
        profile_ref=tmp_path / "profile.local.toml",
        study_id=study_id,
    )

    monkeypatch.setattr(
        materializer,
        "current_owner_callable_adapters",
        lambda **_: {"domain_progress_transition_requests": [dict(dispatch)]},
    )

    canonical_request_tasks = module.paper_recovery_default_executor_dispatch_tasks(
        current_progress=current_progress,
        profile=profile,
        profile_ref=tmp_path / "profile.local.toml",
        study_id=study_id,
    )

    assert owner_callable_only_tasks == []
    assert len(canonical_request_tasks) == 1
    task = canonical_request_tasks[0]
    assert task["task_kind"] == "domain_owner/default-executor-dispatch"
    assert task["provider_admission_pending"] is False
    assert task["provider_admission_requires_opl_runtime_result"] is True
    assert task["opl_domain_progress_transition_request"]["target_runtime_owner"] == "one-person-lab"
    assert task["payload"]["default_executor_dispatch_request"]["dispatch_status"] == (
        "transition_request_pending"
    )


def test_current_default_executor_dispatch_preview_api_is_physically_retired() -> None:
    materializer = importlib.import_module("med_autoscience.controllers.domain_action_request_materializer")

    assert not hasattr(materializer, "current_default_executor_dispatches")
    assert hasattr(materializer, "current_owner_callable_adapters")

    try:
        importlib.import_module(
            "med_autoscience.controllers.domain_action_request_materializer_parts.current_default_executor_dispatches"
        )
    except ModuleNotFoundError:
        return
    raise AssertionError("legacy current_default_executor_dispatches part module must stay retired")
