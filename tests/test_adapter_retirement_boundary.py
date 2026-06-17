from __future__ import annotations

import json
import importlib
from pathlib import Path


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
        "default_executor_execution_latest_wire_projection",
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
        "owner_callable_adapters plus OPL DomainProgressTransitionRuntime durable carrier"
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

    legacy_alias = surfaces["owner_callable_adapter_legacy_dispatch_projection_alias"]
    assert legacy_alias["retained_mas_role"] == "none_physically_retired_no_alias"
    assert legacy_alias["replacement_surface"] == (
        "explicit owner_callable_adapters projection plus OPL DomainProgressTransitionRuntime readback"
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
