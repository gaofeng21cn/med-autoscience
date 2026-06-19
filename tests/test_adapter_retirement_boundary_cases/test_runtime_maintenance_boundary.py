from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[2]


def _inventory() -> dict:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    return json.loads(inventory_path.read_text(encoding="utf-8"))


def _surface(inventory: dict, surface_id: str) -> dict:
    return {
        item["surface_id"]: item for item in inventory["surfaces"]
    }[surface_id]


def test_runtime_lifecycle_payload_retention_requires_bound_opl_authorization() -> None:
    inventory = _inventory()
    lifecycle = _surface(inventory, "runtime_lifecycle_payload_retention")

    assert lifecycle["current_disposition"] == (
        "opl_authorized_maintenance_callable_adapter_live_takeover_tail_open"
    )
    assert lifecycle["retained_mas_role"] == "maintenance_callable_adapter_and_body_free_receipt_projection"
    assert lifecycle["authority_boundary"] == {
        "can_create_opl_command": False,
        "can_create_opl_event": False,
        "can_create_opl_outbox": False,
        "can_create_opl_stage_run": False,
        "can_claim_runtime_currentness": False,
        "can_authorize_generic_cleanup_policy": False,
        "can_authorize_artifact_mutation": False,
        "can_authorize_publication_ready": False,
        "can_write_domain_truth": False,
        "can_write_publication_eval": False,
        "can_write_controller_decision": False,
        "stores_body": False,
        "mutates_derived_runtime_lifecycle_payload_only_when_opl_authorized": True,
    }
    assert lifecycle["apply_gate"] == {
        "required_authorization_surface": "opl_runtime_lifecycle_maintenance_authorization",
        "proof_surface": "opl_runtime_lifecycle_maintenance_authorization_proof",
        "required_for_apply": True,
        "dry_run_requires_authorization": False,
        "must_bind": [
            "operation",
            "maintenance_surface",
            "db_path",
            "outcome",
            "authorization_ref",
        ],
        "missing_or_invalid_authorization_status": (
            "blocked_opl_runtime_lifecycle_maintenance_authorization_required"
        ),
        "typed_blocker": "opl_runtime_lifecycle_maintenance_authorization_required",
        "applies_to_operations": [
            "payload_retention",
            "sqlite_sidecar_repair",
        ],
    }
    assert "runtime_storage_apply_as_runtime_ready" in lifecycle["forbidden_claims"]
    assert "runtime_storage_apply_as_paper_progress" in lifecycle["forbidden_claims"]
    assert lifecycle["retirement_gate"]["live_opl_cleanup_policy_takeover_required"] is True


def test_runtime_lifecycle_payload_retention_rejects_mas_cleanup_authority_regression() -> None:
    inventory = _inventory()
    lifecycle = _surface(inventory, "runtime_lifecycle_payload_retention")
    lifecycle["authority_boundary"]["can_authorize_generic_cleanup_policy"] = True
    lifecycle["authority_boundary"][
        "mutates_derived_runtime_lifecycle_payload_only_when_opl_authorized"
    ] = False
    lifecycle["apply_gate"]["required_for_apply"] = False
    lifecycle["apply_gate"]["dry_run_requires_authorization"] = True
    lifecycle["apply_gate"]["must_bind"].remove("authorization_ref")
    lifecycle["apply_gate"]["applies_to_operations"].remove("sqlite_sidecar_repair")
    lifecycle["forbidden_claims"].remove("runtime_storage_apply_as_paper_progress")
    lifecycle["retirement_gate"]["live_opl_cleanup_policy_takeover_required"] = False
    lifecycle["retirement_gate"]["no_active_caller_required_before_physical_delete"] = False

    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )
    violations = retirement.validate_runtime_surface_retirement_inventory(inventory)

    assert {
        (
            "runtime_lifecycle_payload_retention",
            (
                "truthy_authority_flag:authority_boundary."
                "can_authorize_generic_cleanup_policy"
            ),
        ),
        (
            "runtime_lifecycle_payload_retention",
            "lifecycle_retention_authority_forbidden:can_authorize_generic_cleanup_policy",
        ),
        (
            "runtime_lifecycle_payload_retention",
            "lifecycle_retention_missing_opl_authorized_mutation_flag",
        ),
        (
            "runtime_lifecycle_payload_retention",
            "lifecycle_retention_apply_gate_mismatch:required_for_apply",
        ),
        (
            "runtime_lifecycle_payload_retention",
            "lifecycle_retention_apply_gate_mismatch:dry_run_requires_authorization",
        ),
        (
            "runtime_lifecycle_payload_retention",
            "lifecycle_retention_apply_gate_bindings_incomplete",
        ),
        (
            "runtime_lifecycle_payload_retention",
            "lifecycle_retention_apply_gate_operations_incomplete",
        ),
        (
            "runtime_lifecycle_payload_retention",
            "lifecycle_retention_forbidden_claims_incomplete",
        ),
        (
            "runtime_lifecycle_payload_retention",
            "lifecycle_retention_missing_live_opl_takeover_gate",
        ),
        (
            "runtime_lifecycle_payload_retention",
            "lifecycle_retention_missing_no_active_caller_gate",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in violations}


def test_runtime_storage_maintenance_requires_opl_authorized_physical_apply() -> None:
    inventory = _inventory()
    storage = _surface(inventory, "runtime_storage_maintenance")

    assert storage["current_disposition"] == (
        "opl_authorized_storage_maintenance_callable_adapter_live_takeover_tail_open"
    )
    assert storage["retained_mas_role"] == (
        "maintenance_callable_adapter_and_body_free_diagnostic_projection"
    )
    assert storage["authority_boundary"] == {
        "can_create_opl_command": False,
        "can_create_opl_event": False,
        "can_create_opl_outbox": False,
        "can_create_opl_stage_run": False,
        "can_claim_runtime_currentness": False,
        "can_claim_paper_progress": False,
        "can_authorize_generic_cleanup_policy": False,
        "can_authorize_artifact_mutation": False,
        "can_authorize_publication_ready": False,
        "can_write_domain_truth": False,
        "can_write_publication_eval": False,
        "can_write_controller_decision": False,
        "stores_body": False,
        "dry_run_projection_only": True,
        "mutates_runtime_storage_payload_only_when_opl_authorized": True,
    }
    assert storage["apply_gate"]["required_authorization_surface"] == (
        "opl_runtime_storage_maintenance_authorization"
    )
    assert storage["apply_gate"]["proof_surface"] == (
        "opl_runtime_storage_maintenance_authorization_proof"
    )
    assert storage["apply_gate"]["required_for_workspace_apply"] is True
    assert storage["apply_gate"]["required_for_direct_quest_physical_apply"] is True
    assert storage["apply_gate"]["restore_proof_canary_requires_authorization"] is False
    assert storage["apply_gate"]["refs_only_state_index_only_requires_authorization"] is False
    assert set(storage["apply_gate"]["must_bind"]) == {
        "operation",
        "maintenance_surface",
        "workspace_root_or_quest_root",
        "outcome",
        "authorization_ref",
    }
    assert {
        "workspace_storage_audit_dry_run",
        "restore_proof_canary_source_retained",
        "refs_only_state_index_only_projection",
        "archive_retention_plan",
        "report_retention_plan",
        "attempt_evidence_capsule_plan",
        "semantic_process_retention_plan",
    } <= set(storage["allowed_without_opl_authorization"])
    assert "runtime_storage_apply_as_runtime_ready" in storage["forbidden_claims"]
    assert "runtime_storage_apply_as_provider_admission" in storage["forbidden_claims"]
    assert storage["retirement_gate"]["live_opl_storage_policy_takeover_required"] is True


def test_runtime_storage_maintenance_rejects_mas_storage_authority_regression() -> None:
    inventory = _inventory()
    storage = _surface(inventory, "runtime_storage_maintenance")
    storage["authority_boundary"]["can_claim_paper_progress"] = True
    storage["authority_boundary"]["dry_run_projection_only"] = False
    storage["authority_boundary"]["mutates_runtime_storage_payload_only_when_opl_authorized"] = False
    storage["apply_gate"]["required_for_workspace_apply"] = False
    storage["apply_gate"]["required_for_direct_quest_physical_apply"] = False
    storage["apply_gate"]["restore_proof_canary_requires_authorization"] = True
    storage["apply_gate"]["must_bind"].remove("workspace_root_or_quest_root")
    storage["apply_gate"]["applies_to_operations"].remove("workspace_root_git_retirement_apply")
    storage["apply_gate"]["accepted_operations"].remove("quest_runtime_storage_apply")
    storage["apply_gate"]["accepted_maintenance_surfaces"].remove(
        "quest_runtime_storage_maintenance"
    )
    storage["allowed_without_opl_authorization"].remove("refs_only_state_index_only_projection")
    storage["forbidden_claims"].remove("runtime_storage_apply_as_provider_admission")
    storage["retirement_gate"]["live_opl_storage_policy_takeover_required"] = False
    storage["retirement_gate"]["completion_claim_requires_live_owner_or_opl_readback"] = False

    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )
    violations = retirement.validate_runtime_surface_retirement_inventory(inventory)

    assert {
        (
            "runtime_storage_maintenance",
            "truthy_authority_flag:authority_boundary.can_claim_paper_progress",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_authority_forbidden:can_claim_paper_progress",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_missing_dry_run_projection_boundary",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_missing_opl_authorized_mutation_flag",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_apply_gate_mismatch:required_for_workspace_apply",
        ),
        (
            "runtime_storage_maintenance",
            (
                "storage_maintenance_apply_gate_mismatch:"
                "required_for_direct_quest_physical_apply"
            ),
        ),
        (
            "runtime_storage_maintenance",
            (
                "storage_maintenance_apply_gate_mismatch:"
                "restore_proof_canary_requires_authorization"
            ),
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_apply_gate_bindings_incomplete",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_apply_gate_operations_incomplete",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_accepted_operations_incomplete",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_accepted_surfaces_incomplete",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_allowed_without_auth_incomplete",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_forbidden_claims_incomplete",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_missing_live_opl_takeover_gate",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_missing_live_readback_completion_gate",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in violations}
