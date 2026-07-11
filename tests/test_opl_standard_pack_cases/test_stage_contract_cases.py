from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _read_contract(name: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / "contracts" / f"{name}.json").read_text(encoding="utf-8"))


def test_pack_compiler_input_declares_canonical_agent_identity() -> None:
    materialized = _read_contract("pack_compiler_input")

    assert materialized["canonical_agent_id"] == "mas"
    assert materialized["domain_id"] == "mas"


def test_domain_owner_answer_projection_profile_is_domain_owned_and_refs_only() -> None:
    descriptor = _read_contract("domain_descriptor")
    profile = _read_contract("domain_owner_answer_projection_profile")

    assert descriptor["standard_contract_refs"]["domain_owner_answer_projection_profile"] == (
        "contracts/domain_owner_answer_projection_profile.json"
    )
    assert profile["surface_kind"] == "opl_domain_owner_answer_projection_profile"
    assert profile["version"] == "domain-owner-answer-projection-profile.v1"
    assert profile["profile_role"] == "registry"
    assert profile["domain_id"] == "medautoscience"
    assert profile["binding_project_id"] == "medautoscience"
    assert profile["checkout_currentness_required"] is True
    assert profile["projection_relative_path"] == [
        "artifacts",
        "stage_outputs",
        "08-publication_package_handoff",
        "projection",
        "current_owner_delta.json",
    ]
    assert profile["authority_boundary"] == {
        "refs_only": True,
        "can_write_domain_truth": False,
        "can_create_owner_receipt": False,
        "can_create_typed_blocker": False,
        "can_claim_domain_ready": False,
        "can_claim_production_ready": False,
    }


def test_opl_standard_pack_declares_single_ordinary_default_stage() -> None:
    stage_manifest = json.loads(
        (REPO_ROOT / "agent/stages/manifest.json").read_text(encoding="utf-8")
    )
    profile = _read_contract("golden_path_profile")

    stages = stage_manifest["stages"]
    assert isinstance(stages, list)
    default_stage_ids = [stages[0]["stage_id"]]

    assert default_stage_ids == profile["ordinary_path"]["stage_refs"] == [
        "direction_and_route_selection"
    ]
    assert profile["ordinary_path"]["path_role"] == "ordinary_default"
    assert profile["default_surface_policy"]["ordinary_route_count"] == 1
