from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def _domain_authority_surface() -> dict[str, object]:
    inventory = json.loads(
        (REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json").read_text(
            encoding="utf-8"
        )
    )
    return {item["surface_id"]: item for item in inventory["surfaces"]}[
        "domain_authority_refs_index"
    ]


def test_retired_domain_authority_refs_index_preserves_provenance_scans() -> None:
    surface = _domain_authority_surface()
    bridge = surface["opl_state_index_takeover_bridge"]

    assert surface["current_disposition"] == "physically_retired"
    assert surface["tombstone_or_provenance_ref"].endswith("#domain_authority_refs_index")
    assert bridge["legacy_helper_active_caller_scan"]["active_callers"] == []
    assert bridge["legacy_helper_active_caller_scan"]["physical_delete_allowed"] is False

    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )
    audit = retirement.audit_runtime_surface_retirement_inventory(
        json.loads(
            (REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json").read_text(
                encoding="utf-8"
            )
        )
    )
    assert "domain_authority_refs_index" not in audit["open_surface_ids"]
    assert audit["live_runtime_readiness_completion"]["completion_claim_allowed"] is False


def test_domain_authority_refs_index_runtime_active_private_state_index_scan_is_closed() -> None:
    scan = _domain_authority_surface()["opl_state_index_takeover_bridge"][
        "runtime_active_private_state_index_caller_scan"
    ]

    assert scan["status"] == "no_runtime_active_private_state_index_callers"
    assert scan["runtime_active_caller_count"] == 0
    assert scan["active_runtime_callers"] == []
    assert scan["physical_delete_allowed"] is False
