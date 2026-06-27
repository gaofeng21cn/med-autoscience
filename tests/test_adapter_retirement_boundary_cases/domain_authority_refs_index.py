from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_retired_domain_authority_refs_index_preserves_provenance_scans() -> None:
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
    }["domain_authority_refs_index"]
    scan = surface["opl_state_index_takeover_bridge"]["legacy_helper_active_caller_scan"]
    runtime_scan = surface["opl_state_index_takeover_bridge"][
        "runtime_active_private_state_index_caller_scan"
    ]

    assert runtime_scan["status"] == "no_runtime_active_private_state_index_callers"
    assert runtime_scan["no_runtime_active_private_state_index_caller_proven"] is True
    assert runtime_scan["runtime_active_caller_count"] == 0
    assert runtime_scan["active_runtime_callers"] == []
    assert runtime_scan["physical_delete_allowed"] is False
    assert "runtime_active_no_private_caller_as_physical_delete" in runtime_scan[
        "forbidden_completion_claims"
    ]
    assert scan["status"] == "no_active_replay_or_local_inspection_callers"
    assert scan["no_active_replay_or_local_inspection_caller_proven"] is True
    assert scan["physical_delete_allowed"] is False
    assert (
        scan["required_before_physical_delete"]
        == (
            "domain_authority_refs_index_live_state_index_takeover_or_"
            "no_active_replay_local_inspection_caller_physical_delete_ref"
        )
    )
    assert scan["active_callers"] == []
    assert {
        (
            "paper_progress_transition_refs.record_paper_progress_transition_ref::"
            "persist_authority_refs_index_explicit_opt_in"
        ),
    } <= set(scan["retired_callers"])
    assert "explicit_history_replay" in scan["allowed_consumption"]
    assert "explicit_local_refs_inspection" in scan["allowed_consumption"]
    assert "legacy_helper_no_active_scan_as_physical_delete" in scan[
        "forbidden_completion_claims"
    ]
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
        "docs/history/runtime/mas-private-surface-retirement.md#domain_authority_refs_index"
    )

    audit = retirement.audit_runtime_surface_retirement_inventory(inventory)
    assert "domain_authority_refs_index" not in audit["open_surface_ids"]
    assert audit["completion_claim_allowed"] is True
    assert audit["repo_source_retirement_completion"]["completion_claim_allowed"] is True
    assert audit["live_runtime_readiness_completion"]["completion_claim_allowed"] is False

    bad_inventory = json.loads(json.dumps(inventory))
    bad_surface = {
        item["surface_id"]: item for item in bad_inventory["surfaces"]
    }["domain_authority_refs_index"]
    del bad_surface["tombstone_or_provenance_ref"]

    violations = retirement.validate_runtime_surface_retirement_inventory(bad_inventory)

    assert {
        (
            "domain_authority_refs_index",
            "physically_retired_missing_tombstone_or_provenance_ref",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in violations}


def test_domain_authority_refs_index_runtime_active_private_state_index_scan_is_closed() -> None:
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
    }["domain_authority_refs_index"]
    scan = surface["opl_state_index_takeover_bridge"][
        "runtime_active_private_state_index_caller_scan"
    ]

    assert scan == {
        "status": "no_runtime_active_private_state_index_callers",
        "no_runtime_active_private_state_index_caller_proven": True,
        "runtime_active_caller_count": 0,
        "active_runtime_callers": [],
        "current_runtime_caller_route": (
            "med_autoscience.runtime_protocol.opl_state_index_source_adapter"
        ),
        "legacy_helper_status": "history_replay_or_local_inspection_only_tail_open",
        "physical_delete_allowed": False,
        "forbidden_completion_claims": [
            "runtime_active_no_private_caller_as_physical_delete",
            "history_replay_opt_in_as_runtime_active_caller",
            "source_adapter_manifest_as_live_opl_state_index_readback",
        ],
    }

    audit = retirement.audit_runtime_surface_retirement_inventory(inventory)
    assert "domain_authority_refs_index" not in audit["open_surface_ids"]
    assert audit["physical_delete_allowed"] is False
    assert audit["completion_claim_allowed"] is True
    assert audit["live_runtime_readiness_completion"]["completion_claim_allowed"] is False

    bad_inventory = json.loads(json.dumps(inventory))
    bad_surface = {
        item["surface_id"]: item for item in bad_inventory["surfaces"]
    }["domain_authority_refs_index"]
    del bad_surface["tombstone_or_provenance_ref"]

    assert (
        {
            "surface_id": "domain_authority_refs_index",
            "reason": "physically_retired_missing_tombstone_or_provenance_ref",
        }
        in retirement.validate_runtime_surface_retirement_inventory(bad_inventory)
    )
