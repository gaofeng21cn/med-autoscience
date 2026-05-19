from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE_PATH = REPO_ROOT / "contracts" / "production_acceptance" / "mas-production-acceptance.json"


def _acceptance() -> dict[str, object]:
    return json.loads(ACCEPTANCE_PATH.read_text(encoding="utf-8"))


def _walk_dicts(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def test_mas_production_acceptance_surface_exists_and_records_domain_owned_tail_closure() -> None:
    payload = _acceptance()

    assert payload["surface_kind"] == "mas_domain_owned_production_acceptance"
    assert payload["domain_id"] == "med-autoscience"
    assert payload["owner"] == "MedAutoScience"
    assert payload["acceptance_status"] in {
        "closed_by_domain_owned_acceptance_receipt",
        "domain_owned_typed_blocker_with_next_verification_ref",
    }

    scope = payload["acceptance_scope"]
    assert scope["production_live_soak_not_claimed_by_conformance"] == payload["acceptance_status"]
    assert scope["domain_ready_not_claimed_by_conformance"] == payload["acceptance_status"]
    assert scope["domain_readiness_owner"] == "MedAutoScience"
    assert scope["structural_conformance_already_passed"] is True
    assert scope["physical_conformance_already_passed"] is True
    assert scope["production_like_receipt_chain_present"] is True
    assert scope["publication_or_medical_ready_claimed"] is False


def test_mas_production_acceptance_is_refs_only() -> None:
    payload = _acceptance()

    policy = payload["refs_only_policy"]
    assert policy["body_included"] is False
    assert policy["all_evidence_entries_must_be_refs"] is True
    assert set(policy["forbidden_body_fields"]) == {
        "claim_body",
        "memory_body",
        "artifact_body",
        "publication_verdict_body",
        "medical_ready_body",
        "current_package_body",
    }
    assert not (set(policy["forbidden_body_fields"]) & set(payload))

    ref_entries = [
        item
        for item in _walk_dicts(payload)
        if isinstance(item.get("ref"), str) and item.get("role")
    ]
    assert ref_entries
    assert all(item["body_included"] is False for item in ref_entries)
    assert all(set(item) <= {"ref", "role", "body_included"} for item in ref_entries)


def test_opl_and_provider_completion_do_not_authorize_mas_domain_ready() -> None:
    payload = _acceptance()
    conformance = payload["conformance_evidence"]
    boundary = payload["authority_boundary"]

    assert conformance["structural_conformance_status"] == "passed"
    assert conformance["physical_conformance_status"] == "passed"
    assert set(conformance["does_not_authorize"]) == {
        "domain_ready",
        "publication_ready",
        "medical_ready",
        "artifact_mutation",
        "current_package_update",
    }
    assert boundary["opl_can_authorize_domain_ready"] is False
    assert boundary["provider_completion_is_domain_ready"] is False
    assert boundary["provider_completion_is_publication_ready"] is False
    assert boundary["provider_completion_is_medical_ready"] is False
    assert boundary["structural_conformance_is_domain_ready"] is False
    assert boundary["physical_conformance_is_domain_ready"] is False
    assert boundary["publication_ready_requires_mas_quality_publication_gate"] is True
    assert boundary["medical_ready_requires_mas_quality_publication_gate"] is True
    assert "opl_authorizes_domain_ready" in payload["forbidden_claims"]
    assert "provider_completion_authorizes_medical_ready" in payload["forbidden_claims"]


def test_acceptance_requires_owner_receipt_or_typed_blocker_and_next_verification() -> None:
    payload = _acceptance()
    receipt = payload["domain_acceptance_receipt"]

    owner_receipt_refs = receipt["owner_receipt_refs"]
    typed_blocker_refs = receipt["typed_blocker_refs"]
    next_verification = receipt["next_verification_command_refs"]

    assert owner_receipt_refs or typed_blocker_refs
    assert next_verification
    assert {item["role"] for item in next_verification} == {
        "focused_contract_test",
        "minimum_repo_verification",
        "whitespace_integrity_check",
    }
    assert payload["authority_boundary"][
        "domain_ready_requires_mas_owner_receipt_or_typed_blocker"
    ] is True

    if payload["acceptance_status"] == "closed_by_domain_owned_acceptance_receipt":
        assert receipt["receipt_class"] == "owner_receipt"
        assert receipt["receipt_status"] == "accepted"
        assert owner_receipt_refs
    else:
        assert typed_blocker_refs
        assert payload["consumer_contract"]["current_evidence_tail_status"] == (
            "domain_owned_typed_blocker_with_next_verification_ref"
        )


def test_codex_first_landing_program_is_parallel_and_contract_light() -> None:
    payload = _acceptance()
    program = payload["codex_first_landing_program"]

    assert program["program_id"] == "mas-codex-first-one-shot-landing"
    assert program["program_status"] == "ready_for_parallel_landing"
    assert program["landing_model"] == "parallel_lanes_absorbed_to_main_after_focused_receipts"
    end_state = program["end_state"]
    assert end_state["default_executor"] == "Codex CLI"
    assert end_state["stage_unit"] == "domain_stage"
    assert end_state["agent_shape"] == (
        "Declarative Medical Research Pack + OPL generated/hosted surfaces + minimal authority functions"
    )
    assert end_state["contract_posture"] == "contract_light_ai_first_quality_owner"
    assert end_state["domain_ready_authority"] == "MedAutoScience owner receipt or typed blocker"
    assert end_state["publication_ready_authority"] == (
        "independent MAS AI reviewer/auditor quality gate"
    )
    assert end_state["current_package_authority"] == "MAS artifact authority receipt"

    parallel = program["parallel_execution_model"]
    assert parallel["lanes_can_run_in_parallel"] is True
    assert parallel["merge_policy"] == "absorb_lane_after_focused_validation_then_cleanup_worktree"
    assert set(parallel["shared_blockers"]) == {
        "no_active_caller_proof_missing",
        "opl_generated_surface_parity_missing",
        "domain_receipt_parity_missing",
        "independent_reviewer_or_auditor_receipt_missing",
        "no_forbidden_write_proof_missing",
    }
    assert parallel["main_absorb_requires"] == [
        "git diff --check",
        "focused_lane_tests",
        "scripts/verify.sh",
        "worktree_cleanup",
    ]


def test_codex_first_landing_lanes_cover_pack_caller_physical_canary_and_soak() -> None:
    payload = _acceptance()
    program = payload["codex_first_landing_program"]
    lanes = {lane["lane_id"]: lane for lane in program["lanes"]}

    assert list(lanes) == [
        "codex_stage_pack_quality_lift",
        "opl_generated_default_caller_cutover",
        "physical_source_morphology_retirement",
        "real_paper_line_provider_canary",
        "memory_artifact_human_gate_scaleout",
        "provider_slo_long_soak",
    ]
    assert {lane["execution_owner"] for lane in lanes.values()} == {"Codex CLI"}
    assert lanes["codex_stage_pack_quality_lift"]["owner"] == "MedAutoScience"
    assert "agent/prompts" in lanes["codex_stage_pack_quality_lift"]["primary_surfaces"]
    assert any(
        "independent reviewer/auditor records" in criterion
        for criterion in lanes["codex_stage_pack_quality_lift"]["done_criteria"]
    )
    assert lanes["opl_generated_default_caller_cutover"]["owner"] == "one-person-lab"
    assert "OPL-generated or hosted shell is the default caller" in lanes[
        "opl_generated_default_caller_cutover"
    ]["done_criteria"]
    physical = lanes["physical_source_morphology_retirement"]
    assert physical["owner"] == "MedAutoScience"
    assert "runtime_transport/mas_runtime_core*" in physical["primary_surfaces"]
    assert any("no-active-caller" in criterion for criterion in physical["done_criteria"])
    canary = lanes["real_paper_line_provider_canary"]
    assert "provider completion never claims domain ready" in " ".join(canary["done_criteria"])
    scaleout = lanes["memory_artifact_human_gate_scaleout"]
    assert {"publication-route memory writeback receipts", "artifact lifecycle receipts"} <= set(
        scaleout["primary_surfaces"]
    )
    soak = lanes["provider_slo_long_soak"]
    assert soak["owner"] == "one-person-lab"
    assert "Temporal provider residency" in soak["primary_surfaces"]


def test_codex_first_landing_program_keeps_forbidden_shortcuts_closed() -> None:
    payload = _acceptance()
    program = payload["codex_first_landing_program"]

    assert set(program["forbidden_landing_shortcuts"]) == {
        "replace_codex_stage_work_with_fixed_script_pipeline",
        "treat_descriptor_ready_as_production_ready",
        "treat_provider_completion_as_domain_ready",
        "let_executor_self_review_close_quality_gate",
        "write_memory_body_or_artifact_body_from_opl_projection",
        "keep_legacy_wrapper_or_alias_after_default_caller_cutover",
    }
    assert "treat_provider_completion_as_domain_ready" in program["forbidden_landing_shortcuts"]
    assert payload["authority_boundary"]["provider_completion_is_domain_ready"] is False
    assert payload["authority_boundary"]["opl_can_write_memory_body"] is False
    assert payload["authority_boundary"]["opl_can_write_current_package"] is False
