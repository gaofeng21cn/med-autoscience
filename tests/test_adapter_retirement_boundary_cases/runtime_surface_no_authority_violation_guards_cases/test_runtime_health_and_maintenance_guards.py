from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_runtime_health_and_maintenance_violation_guards() -> None:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )

    runtime_health_bad_inventory = json.loads(json.dumps(inventory))
    runtime_health = next(
        surface
        for surface in runtime_health_bad_inventory["surfaces"]
        if surface["surface_id"] == "runtime_health_kernel"
    )
    runtime_health["local_event_log_append_from_status_payload"] = True
    runtime_health["active_caller_boundary"]["active_caller_retains_runtime_authority"] = True
    runtime_health["active_caller_boundary"][
        "runtime_health_epoch_is_currentness_authority"
    ] = True
    runtime_health["active_caller_boundary"][
        "canonical_runtime_action_is_next_action_authority"
    ] = True
    runtime_health["active_caller_boundary"]["attempt_liveness_owner"] = "med-autoscience"
    runtime_health["diagnostic_projection_boundary"]["can_authorize_provider_admission"] = True
    runtime_health["diagnostic_projection_boundary"]["can_claim_paper_progress"] = True
    runtime_health["diagnostic_projection_boundary"][
        "canonical_runtime_action_is_diagnostic_hint"
    ] = False
    runtime_health["diagnostic_consumer_gate_boundary"][
        "unbound_opl_ref_can_authorize_decision"
    ] = True
    runtime_health["diagnostic_consumer_gate_boundary"][
        "identity_bound_opl_readback_required"
    ] = False
    runtime_health["diagnostic_consumer_gate_boundary"][
        "canonical_runtime_action_hint_can_authorize_recovery"
    ] = True
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "tail_readback_proven"
    ] = True
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "no_active_diagnostic_projection_caller_proven"
    ] = True
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "physical_delete_allowed"
    ] = True
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "mas_runtime_health_snapshot_can_satisfy_readback"
    ] = True
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "required_tail_readback_families_must_match_same_runtime_identity"
    ] = False
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "current_control_or_stage_run_readback_alone_can_satisfy_tail"
    ] = True
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "forbidden_completion_claims"
    ] = []
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "active_diagnostic_projection_caller_scan"
    ]["no_active_diagnostic_projection_caller_proven"] = True
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "active_diagnostic_projection_caller_scan"
    ]["physical_delete_allowed"] = True
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "active_diagnostic_projection_caller_scan"
    ]["allowed_consumption"] = []
    runtime_health["opl_runtime_health_observability_tail_readback"][
        "active_diagnostic_projection_caller_scan"
    ]["forbidden_completion_claims"] = []
    runtime_health["retirement_gate"][
        "runtime_health_live_opl_observability_readback_required"
    ] = False

    runtime_health_violations = retirement.validate_runtime_surface_retirement_inventory(
        runtime_health_bad_inventory
    )

    assert {
        (
            "runtime_health_kernel",
            "runtime_health_status_payload_can_append_event_log",
        ),
        (
            "runtime_health_kernel",
            (
                "truthy_authority_flag:active_caller_boundary."
                "active_caller_retains_runtime_authority"
            ),
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_boundary_forbidden:active_caller_retains_runtime_authority",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_boundary_forbidden:runtime_health_epoch_is_currentness_authority",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_boundary_forbidden:canonical_runtime_action_is_next_action_authority",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_attempt_liveness_owner_not_opl",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_projection_forbidden:can_authorize_provider_admission",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_projection_forbidden:can_claim_paper_progress",
        ),
        (
            "runtime_health_kernel",
            (
                "runtime_health_missing_diagnostic_hint_boundary:"
                "canonical_runtime_action_is_diagnostic_hint"
            ),
        ),
        (
            "runtime_health_kernel",
            (
                "runtime_health_consumer_gate_forbidden:"
                "unbound_opl_ref_can_authorize_decision"
            ),
        ),
        (
            "runtime_health_kernel",
            (
                "runtime_health_consumer_gate_missing:"
                "identity_bound_opl_readback_required"
            ),
        ),
        (
            "runtime_health_kernel",
            (
                "runtime_health_consumer_gate_forbidden:"
                "canonical_runtime_action_hint_can_authorize_recovery"
            ),
        ),
        (
            "runtime_health_kernel",
            "runtime_health_missing_live_opl_observability_gate",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_tail_must_not_claim_readback_proven",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_tail_must_not_claim_no_active_caller",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_tail_must_not_allow_physical_delete",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_tail_forbidden:mas_runtime_health_snapshot_can_satisfy_readback",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_tail_missing_same_identity_family_gate",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_tail_allows_generic_readback_as_tail",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_tail_missing_false_completion_guards",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_diagnostic_scan_must_not_claim_no_active",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_diagnostic_scan_blocks_physical_delete",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_diagnostic_no_active_claim_contradicts_callers",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_diagnostic_callers_block_physical_delete",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_diagnostic_scan_allowed_consumption_incomplete",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_diagnostic_scan_missing_false_completion_guard",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in runtime_health_violations}

    maintenance_bad_inventory = json.loads(json.dumps(inventory))
    maintenance_surfaces = {
        surface["surface_id"]: surface for surface in maintenance_bad_inventory["surfaces"]
    }
    lifecycle_retention = maintenance_surfaces["runtime_lifecycle_payload_retention"]
    lifecycle_retention["opl_runtime_lifecycle_maintenance_tail_readback"][
        "tail_readback_proven"
    ] = True
    lifecycle_retention["opl_runtime_lifecycle_maintenance_tail_readback"][
        "no_active_lifecycle_maintenance_adapter_caller_proven"
    ] = True
    lifecycle_retention["opl_runtime_lifecycle_maintenance_tail_readback"][
        "physical_delete_allowed"
    ] = True
    lifecycle_retention["opl_runtime_lifecycle_maintenance_tail_readback"][
        "apply_authorization_can_satisfy_live_takeover"
    ] = True
    lifecycle_retention["opl_runtime_lifecycle_maintenance_tail_readback"][
        "forbidden_completion_claims"
    ] = []
    storage_maintenance = maintenance_surfaces["runtime_storage_maintenance"]
    storage_maintenance["opl_runtime_storage_maintenance_tail_readback"][
        "tail_readback_proven"
    ] = True
    storage_maintenance["opl_runtime_storage_maintenance_tail_readback"][
        "no_active_storage_maintenance_adapter_caller_proven"
    ] = True
    storage_maintenance["opl_runtime_storage_maintenance_tail_readback"][
        "physical_delete_allowed"
    ] = True
    storage_maintenance["opl_runtime_storage_maintenance_tail_readback"][
        "dry_run_projection_can_satisfy_live_takeover"
    ] = True
    storage_maintenance["opl_runtime_storage_maintenance_tail_readback"][
        "forbidden_completion_claims"
    ] = []

    maintenance_violations = retirement.validate_runtime_surface_retirement_inventory(
        maintenance_bad_inventory
    )

    assert {
        (
            "runtime_lifecycle_payload_retention",
            "lifecycle_retention_tail_must_not_claim_readback_proven",
        ),
        (
            "runtime_lifecycle_payload_retention",
            "lifecycle_retention_tail_must_not_claim_no_active_caller",
        ),
        (
            "runtime_lifecycle_payload_retention",
            "lifecycle_retention_tail_must_not_allow_physical_delete",
        ),
        (
            "runtime_lifecycle_payload_retention",
            "lifecycle_retention_tail_forbidden:apply_authorization_can_satisfy_live_takeover",
        ),
        (
            "runtime_lifecycle_payload_retention",
            "lifecycle_retention_tail_missing_false_completion_guards",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_tail_must_not_claim_readback_proven",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_tail_must_not_claim_no_active_caller",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_tail_must_not_allow_physical_delete",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_tail_forbidden:dry_run_projection_can_satisfy_live_takeover",
        ),
        (
            "runtime_storage_maintenance",
            "storage_maintenance_tail_missing_false_completion_guards",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in maintenance_violations}
