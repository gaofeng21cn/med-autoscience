from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_authority_refs_materializer_execution_wire_and_carrier_violation_guards() -> None:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )

    bad_inventory = json.loads(json.dumps(inventory))
    refs_surface = next(
        surface
        for surface in bad_inventory["surfaces"]
        if surface["surface_id"] == "domain_authority_refs_index"
    )
    refs_surface["active_caller_boundary"]["active_caller_retains_authority"] = True
    refs_surface["retirement_gate"]["active_caller_alone_retains_surface"] = True
    refs_surface["authority_boundary"]["can_authorize_provider_admission"] = True
    refs_surface["opl_state_index_takeover_bridge"]["legacy_helper_active_caller_scan"][
        "active_callers"
    ] = ["paper_progress_transition_refs.record_paper_progress_transition_ref::legacy_sqlite"]
    refs_surface["opl_state_index_takeover_bridge"]["legacy_helper_active_caller_scan"][
        "retired_callers"
    ] = []
    refs_surface["opl_state_index_takeover_bridge"]["legacy_helper_active_caller_scan"][
        "physical_delete_allowed"
    ] = True
    del refs_surface["tombstone_or_provenance_ref"]

    violations = retirement.validate_runtime_surface_retirement_inventory(bad_inventory)

    assert {
        ("domain_authority_refs_index", "truthy_authority_flag:active_caller_boundary.active_caller_retains_authority"),
        ("domain_authority_refs_index", "truthy_authority_flag:authority_boundary.can_authorize_provider_admission"),
        (
            "domain_authority_refs_index",
            "physically_retired_missing_tombstone_or_provenance_ref",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in violations}

    materializer_bad_inventory = json.loads(json.dumps(inventory))
    materializer_surfaces = {
        surface["surface_id"]: surface for surface in materializer_bad_inventory["surfaces"]
    }
    retired_owner_adapter = materializer_surfaces[
        "domain_action_request_materializer_owner_callable_adapter_projection"
    ]
    retired_owner_adapter["legacy_projection_boundary"][
        "owner_callable_adapter_counts_authority"
    ] = True
    del retired_owner_adapter["tombstone_or_provenance_ref"]
    request_tasks = materializer_surfaces[
        "domain_action_request_materializer_request_tasks_projection"
    ]
    request_tasks["projection_boundary"]["body_authority"] = True
    del request_tasks["tombstone_or_provenance_ref"]
    transition_request = materializer_surfaces[
        "domain_action_request_materializer_canonical_transition_request_body_projection"
    ]
    transition_request["projection_boundary"]["transition_request_projection_body_authority"] = True
    del transition_request["tombstone_or_provenance_ref"]

    materializer_violations = retirement.validate_runtime_surface_retirement_inventory(
        materializer_bad_inventory
    )

    assert {
        (
            "domain_action_request_materializer_owner_callable_adapter_projection",
            "physically_retired_missing_tombstone_or_provenance_ref",
        ),
        (
            "domain_action_request_materializer_request_tasks_projection",
            "truthy_authority_flag:projection_boundary.body_authority",
        ),
        (
            "domain_action_request_materializer_canonical_transition_request_body_projection",
            "physically_retired_missing_tombstone_or_provenance_ref",
        ),
        (
            "domain_action_request_materializer_canonical_transition_request_body_projection",
            "truthy_authority_flag:projection_boundary.transition_request_projection_body_authority",
        ),
        (
            "domain_action_request_materializer_request_tasks_projection",
            "physically_retired_missing_tombstone_or_provenance_ref",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in materializer_violations}

    legacy_bad_inventory = json.loads(json.dumps(inventory))
    legacy_latest = next(
        surface
        for surface in legacy_bad_inventory["surfaces"]
        if surface["surface_id"] == "owner_callable_adapter_receipt_latest_wire_projection"
    )
    legacy_latest["legacy_wire_default_reader_fallback_allowed"] = True
    legacy_latest["current_reader_boundary"][
        "owner_callable_receipt_candidates_reads_legacy_wire_by_default"
    ] = True
    legacy_latest["history_replay_boundary"].pop(
        "owner_callable_adapter_receipt_consumption_requires_allow_legacy_fallback"
    )
    del legacy_latest["tombstone_or_provenance_ref"]

    legacy_violations = retirement.validate_runtime_surface_retirement_inventory(legacy_bad_inventory)

    assert {
        (
            "owner_callable_adapter_receipt_latest_wire_projection",
            "physically_retired_missing_tombstone_or_provenance_ref",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in legacy_violations}

    legacy_stage_run_bad_inventory = json.loads(json.dumps(inventory))
    legacy_stage_run = next(
        surface
        for surface in legacy_stage_run_bad_inventory["surfaces"]
        if surface["surface_id"] == "owner_callable_adapter_receipt_latest_wire_projection"
    )
    legacy_stage_run["legacy_stage_run_abi_boundary"][
        "stage_closeout_packets_can_authorize_provider_admission"
    ] = True
    legacy_stage_run["legacy_stage_run_abi_boundary"][
        "stage_closeout_packets_can_authorize_execution"
    ] = True
    legacy_stage_run["legacy_stage_run_abi_boundary"][
        "terminal_closeout_consumption_requires_owner_result_or_typed_blocker"
    ] = False
    legacy_stage_run_scan = legacy_stage_run["legacy_stage_run_abi_boundary"][
        "active_stage_run_abi_caller_scan"
    ]
    legacy_stage_run_scan["no_active_stage_run_abi_caller_proven"] = True
    legacy_stage_run_scan["physical_delete_allowed"] = True
    del legacy_stage_run["tombstone_or_provenance_ref"]

    legacy_stage_run_violations = retirement.validate_runtime_surface_retirement_inventory(
        legacy_stage_run_bad_inventory
    )

    assert {
        (
            "owner_callable_adapter_receipt_latest_wire_projection",
            (
                "truthy_authority_flag:legacy_stage_run_abi_boundary."
                "stage_closeout_packets_can_authorize_provider_admission"
            ),
        ),
        (
            "owner_callable_adapter_receipt_latest_wire_projection",
            (
                "truthy_authority_flag:legacy_stage_run_abi_boundary."
                "stage_closeout_packets_can_authorize_execution"
            ),
        ),
        (
            "owner_callable_adapter_receipt_latest_wire_projection",
            "physically_retired_missing_tombstone_or_provenance_ref",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in legacy_stage_run_violations}

    carrier_bad_inventory = json.loads(json.dumps(inventory))
    legacy_carrier = next(
        surface
        for surface in carrier_bad_inventory["surfaces"]
        if surface["surface_id"] == "owner_callable_dispatch_request"
    )
    legacy_carrier["active_caller_boundary"]["provider_admission_pending"] = True
    legacy_carrier["legacy_stage_run_abi_provenance_boundary"]["mas_can_create_stage_run"] = True
    legacy_carrier["legacy_stage_run_abi_provenance_boundary"][
        "requires_opl_domain_progress_transition_runtime_intake"
    ] = False
    legacy_carrier["legacy_source_contamination_boundary"][
        "source_dispatch_claims_are_diagnostic_only"
    ] = False
    legacy_carrier["legacy_source_contamination_boundary"][
        "polluted_source_payload_can_authorize_provider_admission"
    ] = True
    legacy_carrier["legacy_source_contamination_boundary"]["forbidden_source_claims"].remove(
        "provider_admission_pending"
    )
    legacy_carrier["opl_owner_callable_adapter_carrier_tail_readback"][
        "tail_readback_proven"
    ] = True
    legacy_carrier["opl_owner_callable_adapter_carrier_tail_readback"][
        "transition_request_pending_can_satisfy_readback"
    ] = True
    legacy_carrier["opl_owner_callable_adapter_carrier_tail_readback"][
        "request_only_carrier_can_authorize_provider_admission"
    ] = True
    legacy_carrier["opl_owner_callable_adapter_carrier_tail_readback"][
        "forbidden_completion_claims"
    ].remove("transition_request_pending_as_opl_live_readback")
    del legacy_carrier["tombstone_or_provenance_ref"]

    carrier_violations = retirement.validate_runtime_surface_retirement_inventory(
        carrier_bad_inventory
    )

    assert {
        (
            "owner_callable_dispatch_request",
            "truthy_authority_flag:active_caller_boundary.provider_admission_pending",
        ),
        (
            "owner_callable_dispatch_request",
            "truthy_authority_flag:legacy_stage_run_abi_provenance_boundary.mas_can_create_stage_run",
        ),
        (
            "owner_callable_dispatch_request",
            "truthy_authority_flag:legacy_source_contamination_boundary.polluted_source_payload_can_authorize_provider_admission",
        ),
        (
            "owner_callable_dispatch_request",
            "truthy_authority_flag:opl_owner_callable_adapter_carrier_tail_readback.request_only_carrier_can_authorize_provider_admission",
        ),
        (
            "owner_callable_dispatch_request",
            "physically_retired_missing_tombstone_or_provenance_ref",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in carrier_violations}
