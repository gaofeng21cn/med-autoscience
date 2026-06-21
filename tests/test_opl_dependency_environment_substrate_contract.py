from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = (
    REPO_ROOT
    / "contracts"
    / "opl-framework"
    / "dependency-environment-substrate-contract.json"
)


def _load_contract() -> dict[str, object]:
    payload = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_opl_dependency_environment_contract_keeps_renderer_dependency_as_declaration() -> None:
    contract = _load_contract()

    assert contract["contract_id"] == "opl.dependency_environment_substrate.v1"
    assert contract["state"] == "target_contract"

    principles = contract["core_principles"]
    assert isinstance(principles, dict)
    assert principles["domain_pack_declares_requirements_only"] is True
    assert principles["opl_substrate_solves_locks_prepares_and_caches"] is True
    assert principles["renderer_code_must_not_install_packages"] is True
    assert principles["locks_do_not_authorize_publication_readiness"] is True

    requirement_surface = contract["domain_requirement_surface"]
    assert isinstance(requirement_surface, dict)
    assert requirement_surface["current_mas_ref"].endswith("renderer_dependency_profile.json")
    assert "profiles[].system_requirements" in requirement_surface["required_fields"]
    assert "install_script_to_run_inside_renderer" in requirement_surface["forbidden_fields"]


def test_opl_dependency_environment_contract_declares_required_substrate_surfaces() -> None:
    contract = _load_contract()

    surfaces = {item["surface"]: item for item in contract["opl_surfaces"]}
    assert set(surfaces) == {
        "opl pack env resolve",
        "opl pack env lock",
        "opl pack env prepare",
        "opl pack env doctor",
        "opl pack env run-context",
        "opl pack env cache",
    }
    assert all(item["status"] == "target_planned" for item in surfaces.values())

    lock_contract = contract["lock_contract"]
    assert isinstance(lock_contract, dict)
    assert "container_image_digest" in lock_contract["required_fields"]
    assert "renv" in lock_contract["manager_choices"]
    assert "uv" in lock_contract["manager_choices"]
    assert "mixed_profile" in lock_contract["manager_choices"]

    receipt_contract = contract["prepare_receipt_contract"]
    assert isinstance(receipt_contract, dict)
    assert "run_context_ref" in receipt_contract["required_fields"]
    assert receipt_contract["failure_routes"]["missing_dependency"] == "opl_pack_substrate_issue"
    assert receipt_contract["failure_routes"]["permission_required"] == "human_or_admin_gate_required"


def test_mas_consumption_boundary_forbids_dependency_receipts_as_quality_authority() -> None:
    contract = _load_contract()

    mas_consumption = contract["mas_consumption_contract"]
    assert isinstance(mas_consumption, dict)
    assert mas_consumption["ordinary_display_path_requires_prepared_receipt"] is True
    assert mas_consumption["display_pack_render_must_consume_run_context_ref"] is True
    assert mas_consumption["renderer_may_check_binaries_but_must_not_install"] is True
    assert "dependency_environment_receipt_ref" in mas_consumption["allowed_mas_writes"]
    assert {
        "dependency_environment_receipt_means_publication_ready",
        "dependency_environment_lock_means_visual_audit_clear",
        "dependency_environment_prepared_means_scientific_correctness",
        "renderer_dependency_profile_can_write_study_truth",
    } <= set(mas_consumption["forbidden_mas_claims"])

    security = contract["security_and_update_policy"]
    assert isinstance(security, dict)
    assert security["install_scripts_from_domain_packs_allowed"] is False
    assert security["dependency_updates_require_explicit_lock_refresh"] is True
    assert security["container_digest_required_for_publication_reproducibility"] is True
