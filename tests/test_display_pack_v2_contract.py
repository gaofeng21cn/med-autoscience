from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "contracts" / "display-pack-contract.v2.json"

EXPECTED_PACK_REQUIRED_FIELDS = {
    "pack_id",
    "version",
    "display_api_version",
    "source",
    "owner",
    "license",
    "templates",
    "style_profiles",
    "qc_profiles",
    "ai_policy",
    "goldens",
    "exemplars",
    "provenance",
    "opl_handoff",
}

EXPECTED_TEMPLATE_REQUIRED_FIELDS = {
    "template_id",
    "full_template_id",
    "kind",
    "display_name",
    "paper_family_ids",
    "audit_family",
    "renderer_family",
    "input_schema_ref",
    "qc_profile_ref",
    "style_profile_ref",
    "required_exports",
    "execution_mode",
    "entrypoint",
    "paper_proven",
    "golden_case_paths",
    "exemplar_refs",
}


def _load_contract_payload() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def test_display_pack_v2_root_contract_declares_descriptor_boundaries() -> None:
    from med_autoscience.display_pack_v2_contract import (
        OPL_EXTERNAL_CONSUMER_STATUS,
        OPL_EXTERNAL_CONSUMER_SURFACE,
        OPL_HANDOFF_TAIL_STATUS,
        validate_display_pack_v2_contract,
    )

    payload = validate_display_pack_v2_contract(_load_contract_payload())

    assert payload["schema_version"] == 2
    assert payload["contract_id"] == "display-pack-contract.v2"
    assert set(payload["pack_descriptor"]["required_fields"]) == EXPECTED_PACK_REQUIRED_FIELDS
    assert set(payload["template_descriptor"]["required_fields"]) == EXPECTED_TEMPLATE_REQUIRED_FIELDS

    authority = payload["authority_boundaries"]
    assert authority["mas_pack_descriptor_authority"] is True
    assert authority["mas_publication_quality_authority"] is True
    assert authority["mas_owns_opl_generic_pack_os"] is False
    assert authority["opl_can_write_mas_publication_truth"] is False
    assert authority["display_pack_lock_can_authorize_publication_readiness"] is False

    handoff = payload["opl_handoff"]
    assert handoff["status"] == "handoff_tail"
    assert handoff["tail_status"] == OPL_HANDOFF_TAIL_STATUS
    assert handoff["target_owner"] == "OPL Pack OS"
    assert handoff["external_opl_consumer"]["status"] == OPL_EXTERNAL_CONSUMER_STATUS
    assert handoff["external_opl_consumer"]["surface"] == OPL_EXTERNAL_CONSUMER_SURFACE
    assert handoff["external_opl_consumer"]["verification_refs"]
    assert "paper/figure_spec.json" in payload["quality_surfaces"]["paper_quality_refs"]
    assert "paper/figure_polish_lifecycle.json" in payload["quality_surfaces"]["paper_quality_refs"]


def test_display_pack_v2_validator_rejects_non_object_payload() -> None:
    from med_autoscience.display_pack_v2_contract import validate_display_pack_v2_contract

    with pytest.raises(ValueError, match="must be a JSON object"):
        validate_display_pack_v2_contract(["not", "an", "object"])


def test_display_pack_v2_validator_rejects_missing_descriptor_fields() -> None:
    from med_autoscience.display_pack_v2_contract import validate_display_pack_v2_contract

    payload = _load_contract_payload()
    payload["pack_descriptor"]["required_fields"].remove("ai_policy")

    with pytest.raises(ValueError, match="pack_descriptor.required_fields"):
        validate_display_pack_v2_contract(payload)


def test_display_pack_v2_validator_rejects_landed_opl_tail_status() -> None:
    from med_autoscience.display_pack_v2_contract import validate_display_pack_v2_contract

    payload = copy.deepcopy(_load_contract_payload())
    payload["opl_handoff"]["tail_status"] = "landed"

    with pytest.raises(ValueError, match="opl_handoff.tail_status"):
        validate_display_pack_v2_contract(payload)


def test_display_pack_v2_validator_rejects_missing_external_opl_consumer() -> None:
    from med_autoscience.display_pack_v2_contract import validate_display_pack_v2_contract

    payload = copy.deepcopy(_load_contract_payload())
    del payload["opl_handoff"]["external_opl_consumer"]

    with pytest.raises(ValueError, match="opl_handoff.external_opl_consumer"):
        validate_display_pack_v2_contract(payload)


def test_display_pack_v2_validator_rejects_wrong_external_opl_consumer_surface() -> None:
    from med_autoscience.display_pack_v2_contract import validate_display_pack_v2_contract

    payload = copy.deepcopy(_load_contract_payload())
    payload["opl_handoff"]["external_opl_consumer"]["surface"] = "opl pack os other"

    with pytest.raises(ValueError, match="opl_handoff.external_opl_consumer.surface"):
        validate_display_pack_v2_contract(payload)
