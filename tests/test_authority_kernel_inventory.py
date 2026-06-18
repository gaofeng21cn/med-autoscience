from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
REQUIRED_CATEGORIES = {
    "owner_receipt_signer",
    "typed_blocker_materializer",
    "source_readiness",
    "publication_quality_gate",
    "artifact_mutation_authorization",
    "memory_accept_reject",
    "no_forbidden_write_proof",
    "refs_only_helper",
    "diagnostic_probe",
}
CONTRACT_ONLY_ITEM_OVERLAY_FIELDS = {
    "disposition",
    "no_active_caller",
    "replacement_parity",
    "no_forbidden_write_proof",
    "retirement_gate",
    "tombstone_or_provenance",
}


def _contract() -> dict[str, object]:
    return json.loads(
        (REPO_ROOT / "contracts/authority_kernel_inventory.json").read_text(encoding="utf-8")
    )


def _without_contract_only_overlays(payload: dict[str, object]) -> dict[str, object]:
    managed = dict(payload)
    managed.pop("retirement_gate_policy", None)
    managed["items"] = [
        {
            key: value
            for key, value in dict(item).items()
            if key not in CONTRACT_ONLY_ITEM_OVERLAY_FIELDS
        }
        for item in managed["items"]
    ]
    return managed


def test_authority_kernel_inventory_contract_matches_builder() -> None:
    module = importlib.import_module("med_autoscience.authority_kernel_inventory")

    assert _without_contract_only_overlays(_contract()) == _without_contract_only_overlays(
        module.build_authority_kernel_inventory()
    )


def test_authority_kernel_inventory_contract_retirement_gate_overlay_is_explicit() -> None:
    inventory = _contract()
    policy = inventory["retirement_gate_policy"]

    assert policy["surface_kind"] == "mas_authority_kernel_retirement_gate_policy"
    assert policy["no_active_caller_required_before_delete"] is True
    assert policy["no_forbidden_write_proof_required"] is True
    assert policy["tombstone_or_provenance_required_before_delete"] is True
    assert policy["completion_percent_policy"].startswith(
        "inventory_or_test_green_is_not_100_percent"
    )


def test_authority_kernel_inventory_covers_required_categories_and_fields() -> None:
    module = importlib.import_module("med_autoscience.authority_kernel_inventory")

    inventory = module.build_authority_kernel_inventory()
    items = inventory["items"]
    required_fields = set(inventory["required_item_fields"])

    assert inventory["surface_kind"] == "mas_authority_kernel_inventory"
    assert inventory["contract_id"] == "mas_authority_kernel_inventory.v1"
    assert inventory["state"] == "inventory_landed_physical_thinning_pending"
    assert {item["category"] for item in items} == REQUIRED_CATEGORIES
    assert inventory["counts"]["item_count"] == len(REQUIRED_CATEGORIES)
    assert inventory["counts"]["category_count"] == len(REQUIRED_CATEGORIES)
    assert inventory["counts"]["owner_callable_backed_count"] >= 4
    assert inventory["counts"]["gap_count"] == 0
    assert inventory["gaps"] == []

    for item in items:
        assert required_fields <= set(item), item["item_id"]
        for field in required_fields:
            assert item[field], (item["item_id"], field)
        assert item["cannot_lift_to_opl_reason"]
        assert item.get("retirement_gate") or item.get("upcollect_target")


def test_authority_kernel_inventory_forbidden_authority_is_complete() -> None:
    module = importlib.import_module("med_autoscience.authority_kernel_inventory")
    arsenal = importlib.import_module("med_autoscience.agent_tool_arsenal")

    expected = set(arsenal.FORBIDDEN_DOMAIN_AUTHORITY)
    inventory = module.build_authority_kernel_inventory()

    assert set(inventory["forbidden_domain_authority"]) == expected
    for item in inventory["items"]:
        assert set(item["forbidden_authority"]) == expected, item["item_id"]
        assert "publication_quality" in item["forbidden_authority"]
        assert "artifact_authority" in item["forbidden_authority"]
        assert "memory_accept_reject" in item["forbidden_authority"]


def test_authority_kernel_inventory_does_not_list_generic_runtime_owner_as_retained_authority() -> None:
    module = importlib.import_module("med_autoscience.authority_kernel_inventory")

    inventory = module.build_authority_kernel_inventory()
    forbidden_owners = set(inventory["generic_runtime_owner_names"])

    assert forbidden_owners
    for item in inventory["items"]:
        assert item["owner"] not in forbidden_owners, item["item_id"]
    assert inventory["non_claims"]["authority_fully_retired"] is False
    assert inventory["non_claims"]["physical_thinning_complete"] is False
    assert inventory["non_claims"]["production_ready"] is False


def test_authority_kernel_inventory_references_existing_representative_surfaces() -> None:
    inventory = _contract()
    items = {item["category"]: item for item in inventory["items"]}

    assert "owner_callable:publication_handoff_owner_gate" in items["owner_receipt_signer"][
        "active_caller_refs"
    ]
    assert "typed blocker:medical_paper_readiness_surface_input_required" in items[
        "typed_blocker_materializer"
    ]["output_refs"]
    assert "source_readiness_receipt_refs" in items["source_readiness"]["output_refs"]
    assert "artifacts/publication_eval/latest.json" in items["publication_quality_gate"][
        "allowed_writes"
    ]
    assert "artifact_package_authority_receipt_refs" in items[
        "artifact_mutation_authorization"
    ]["output_refs"]
    assert "publication_route_memory_writeback_receipt_refs" in items["memory_accept_reject"][
        "output_refs"
    ]
    assert "artifacts/publication_eval/latest.json" in items["no_forbidden_write_proof"][
        "forbidden_writes"
    ]
    assert "refs-only advisory candidates" in items["refs_only_helper"]["output_refs"]
    assert "route_back_evidence_ref" in items["diagnostic_probe"]["output_refs"]
