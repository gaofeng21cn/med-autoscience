from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
INVENTORY_PATH = (
    REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
)

EXPECTED_LIVE_TAILS = {
    "stage_outcome_authority": {
        "required_ref_families": {
            "stage_outcome_authority_execute_dispatch_live_readback_ref",
            "stage_outcome_authority_provider_hosted_stage_packet_live_readback_ref",
            "stage_outcome_authority_no_active_owner_callable_adapter_caller_scan_ref",
        },
        "forbidden_completion_interpretations": {
            "repo_authorization_coverage_as_live_every_active_caller_soak",
            "provider_completion_as_dispatch_retirement",
            "provider_handoff_or_completion_as_physical_delete",
        },
    },
    "domain_diagnostic_obligation_actuator": {
        "required_ref_families": {
            "domain_diagnostic_obligation_actuator_opl_obligation_actuator_tail_readback_ref",
            "domain_diagnostic_obligation_actuator_owner_retirement_decision_ref",
            "domain_diagnostic_obligation_actuator_no_active_caller_scan_ref",
        },
        "forbidden_completion_interpretations": {
            "mas_policy_projection_as_opl_recovery_obligation_store_readback",
        },
    },
    "runtime_health_kernel": {
        "required_ref_families": {
            "runtime_health_kernel_opl_runtime_health_observability_tail_readback_ref",
            "runtime_health_kernel_opl_observability_live_readback_ref",
            "runtime_health_kernel_opl_route_reconciler_live_readback_ref",
            "runtime_health_kernel_no_active_diagnostic_projection_caller_physical_delete_ref",
        },
        "forbidden_completion_interpretations": {
            "mas_runtime_health_snapshot_as_opl_observability_readback",
            "runtime_health_snapshot_reader_as_opl_observability_readback",
            "active_diagnostic_projection_scan_as_physical_delete",
        },
    },
    "progress_portal_study_workbench_overview_action_projection": {
        "required_ref_families": {
            (
                "progress_portal_study_workbench_overview_action_projection_"
                "opl_workbench_shell_readback_tail_ref"
            ),
            (
                "progress_portal_study_workbench_overview_action_projection_"
                "opl_workbench_shell_action_transport_readback_ref"
            ),
            (
                "progress_portal_study_workbench_overview_action_projection_"
                "opl_current_control_readback_ref"
            ),
        },
        "forbidden_completion_interpretations": {
            "mas_next_system_action_summary_as_action_transport_readback",
            "operator_intent_refs_as_workbench_action_transport",
        },
    },
    "agent_tool_arsenal_scientific_capability_registry": {
        "required_ref_families": {
            "agent_tool_arsenal_scientific_capability_registry_live_owner_consumption_soak_ref",
            "agent_tool_arsenal_scientific_capability_registry_direct_hosted_parity_ref",
            "agent_tool_arsenal_no_active_registry_projection_caller_scan_ref",
        },
        "forbidden_completion_interpretations": {
            "capability_registry_contract_as_live_owner_consumption_soak",
            "wildcard_guard_as_live_owner_consumption_soak",
            "capability_request_projection_as_paper_progress",
        },
    },
    "runtime_lifecycle_payload_retention": {
        "required_ref_families": {
            "runtime_lifecycle_payload_retention_opl_runtime_lifecycle_maintenance_tail_readback_ref",
            "runtime_lifecycle_payload_retention_opl_runtime_lifecycle_cleanup_policy_live_readback_ref",
        },
        "forbidden_completion_interpretations": {
            "opl_maintenance_authorization_as_live_cleanup_policy_takeover",
        },
    },
    "runtime_storage_maintenance": {
        "required_ref_families": {
            "runtime_storage_maintenance_opl_runtime_storage_maintenance_tail_readback_ref",
            "runtime_storage_maintenance_opl_runtime_storage_policy_live_readback_ref",
            "runtime_storage_maintenance_opl_restore_retention_shell_live_readback_ref",
        },
        "forbidden_completion_interpretations": {
            "runtime_storage_apply_gate_as_live_takeover",
        },
    },
}


def test_runtime_surface_retirement_no_authority_audit_blocks_active_caller_regression() -> None:
    inventory = json.loads(INVENTORY_PATH.read_text(encoding="utf-8"))
    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )

    audit = retirement.audit_runtime_surface_retirement_inventory(inventory)

    assert audit["surface_kind"] == "mas_runtime_surface_retirement_no_authority_audit"
    assert audit["status"] == "repo_source_physical_retirement_complete"
    assert audit["generic_runtime_owner"] == "one-person-lab"
    assert audit["completion_claim_allowed"] is True
    assert audit["repo_source_retirement_completion"]["completion_claim_allowed"] is True
    assert audit["live_runtime_readiness_completion"]["completion_claim_allowed"] is False
    assert audit["repo_no_authority_guard_satisfied"] is True
    assert audit["live_soak_or_no_active_caller_proven"] is False
    assert audit["physical_delete_allowed"] is False
    assert audit["violations"] == []
    assert {
        "repo_source_retirement_as_live_runtime_ready",
        "live_runtime_tail_open_as_repo_source_delete_blocker",
        "active_caller_exists_as_retention_reason",
        "maintenance_apply_gate_as_paper_progress",
    } <= set(audit["forbidden_completion_interpretations"])

    open_surfaces = {surface["surface_id"]: surface for surface in audit["open_surfaces"]}
    assert set(open_surfaces) == set(EXPECTED_LIVE_TAILS)
    assert {
        "domain_authority_refs_index",
        "owner_callable_dispatch_request",
        "owner_callable_adapter_receipt_latest_wire_projection",
    }.isdisjoint(open_surfaces)

    layers = audit["completion_evidence_layers"]
    assert layers["repo_no_authority_guard"]["violations_count"] == 0
    assert layers["live_soak_or_no_active_caller"]["status"] == "evidence_required"
    assert layers["live_soak_or_no_active_caller"]["proven"] is False
    assert layers["physical_retirement"]["allowed"] is False
    assert set(layers["physical_retirement"]["blocked_surface_ids"]) == set(
        EXPECTED_LIVE_TAILS
    )

    evidence_tails = {
        item["surface_id"]: item
        for item in layers["live_soak_or_no_active_caller"]["open_surface_tails"]
    }
    assert set(evidence_tails) == set(EXPECTED_LIVE_TAILS)
    for surface_id, expected in EXPECTED_LIVE_TAILS.items():
        tail = evidence_tails[surface_id]
        assert expected["required_ref_families"] <= set(tail["required_ref_families"])
        assert expected["forbidden_completion_interpretations"] <= set(
            tail["forbidden_completion_interpretations"]
        )

    assert all(
        surface["active_caller_retains_authority"] is False
        for surface in open_surfaces.values()
    )
    assert all(
        surface["active_caller_retains_runtime_authority"] is False
        for surface in open_surfaces.values()
    )
