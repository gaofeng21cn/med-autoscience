from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
ACCEPTANCE_PATH = REPO_ROOT / "contracts" / "production_acceptance" / "mas-production-acceptance.json"
AGENT_LAB_HANDOFF_PATH = REPO_ROOT / "contracts" / "agent_lab_handoff.json"


def _acceptance() -> dict[str, object]:
    return json.loads(ACCEPTANCE_PATH.read_text(encoding="utf-8"))


def _agent_lab_handoff() -> dict[str, object]:
    return json.loads(AGENT_LAB_HANDOFF_PATH.read_text(encoding="utf-8"))


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


def test_acceptance_exposes_paper_line_guarded_apply_scaleout_refs_without_body() -> None:
    payload = _acceptance()
    evidence = payload["paper_line_guarded_apply_evidence"]

    assert evidence["surface_kind"] == "mas_paper_line_guarded_apply_evidence_scaleout"
    assert evidence["lane_id"] == "lane_4a_mas_evidence_scaleout"
    assert evidence["mode"] == "domain_owned_refs_only"
    assert evidence["selected_evidence_surface"] == (
        "product_entry_manifest.provider_guarded_soak_read_model.paper_line_guarded_apply_evidence"
    )
    assert evidence["body_included"] is False
    assert evidence["domain_verdict_claimed"] is False
    assert evidence["provider_completion_is_paper_closure"] is False
    assert evidence["opl_can_write_publication_eval"] is False
    assert evidence["opl_can_write_controller_decisions"] is False
    assert evidence["opl_can_write_artifact_gate"] is False
    assert evidence["opl_can_write_memory_body"] is False
    assert evidence["opl_can_write_final_verdict"] is False
    assert evidence["required_owner_outcome_refs"] == [
        "owner_receipt_ref",
        "progress_delta_ref",
        "ai_reviewer_gate_ref",
        "artifact_movement_ref",
        "human_gate_ref",
        "stop_loss_ref",
        "stable_typed_blocker_ref",
        "no_forbidden_write_proof_ref",
    ]
    outcomes = {item["outcome_id"]: item for item in evidence["domain_owned_outcome_refs"]}
    assert set(outcomes) == {
        "progress_delta",
        "ai_reviewer_gate_movement",
        "artifact_movement",
        "human_gate",
        "stop_loss",
        "stable_typed_blocker",
    }
    assert outcomes["progress_delta"]["owner_surface_role"] == "progress_delta_ref"
    assert outcomes["ai_reviewer_gate_movement"]["owner_surface_role"] == "ai_reviewer_gate_ref"
    assert outcomes["artifact_movement"]["owner_surface_role"] == "artifact_movement_ref"
    assert outcomes["human_gate"]["owner_surface_role"] == "human_gate_ref"
    assert outcomes["stop_loss"]["owner_surface_role"] == "stop_loss_ref"
    assert outcomes["stable_typed_blocker"]["owner_surface_role"] == "stable_typed_blocker_ref"
    assert all(item["domain_owned"] is True for item in outcomes.values())
    assert all(item["body_included"] is False for item in outcomes.values())
    assert all(item["write_permitted"] is False for item in outcomes.values())
    assert all(item["opl_projection_only"] is True for item in outcomes.values())
    assert set(evidence["forbidden_body_surfaces"]) == {
        "publication_eval_body",
        "controller_decision_body",
        "artifact_gate_body",
        "memory_body",
        "final_verdict_body",
    }
    opl_contract = evidence["opl_ingestable_ref_contract"]
    assert opl_contract == {
        "ref_packet_role": "opl_agent_lab_evidence_scaleout_input",
        "selected_surface": "existing_mas_paper_line_guarded_apply_evidence",
        "allowed_ref_roles": [
            "owner_receipt_ref",
            "progress_delta_ref",
            "ai_reviewer_gate_receipt_ref",
            "artifact_movement_ref",
            "human_gate_or_resume_ref",
            "stable_typed_blocker_ref",
            "no_forbidden_write_proof_ref",
        ],
        "closeout_requires_mas_owner_receipt_or_typed_blocker": True,
        "opl_may_persist_refs_only": True,
        "opl_may_write_domain_truth": False,
        "opl_may_write_memory_body": False,
        "opl_may_write_artifact_body": False,
        "opl_may_authorize_publication_or_quality": False,
    }
    packets = {item["required_role"]: item for item in evidence["scaleout_ref_packets"]}
    assert set(packets) == {
        "owner_receipt_ref",
        "progress_delta_ref",
        "ai_reviewer_gate_receipt_ref",
        "artifact_movement_ref",
        "human_gate_or_resume_ref",
        "stable_typed_blocker_ref",
        "no_forbidden_write_proof_ref",
    }
    assert packets["owner_receipt_ref"]["owner_surface"] == (
        "artifacts/runtime/owner_route/latest.json"
    )
    assert packets["progress_delta_ref"]["owner_surface"] == (
        "artifacts/controller/repair_execution_evidence/latest.json"
    )
    assert packets["progress_delta_ref"]["fallback_owner_surface"] == (
        "artifacts/runtime/turn_closeouts/<active_run_id>.json"
    )
    assert packets["ai_reviewer_gate_receipt_ref"]["owner_surface"] == (
        "artifacts/publication_eval/latest.json"
    )
    assert packets["artifact_movement_ref"]["owner_surface"] == "artifact_authority_receipt"
    assert packets["human_gate_or_resume_ref"]["fallback_owner_surface"] == (
        "human_gate_resume_receipt"
    )
    assert packets["no_forbidden_write_proof_ref"]["owner_surface"] == (
        "product_entry_manifest.provider_guarded_soak_read_model.no_forbidden_write_proof"
    )
    assert all(item["body_included"] is False for item in packets.values())
    assert all(item["opl_ingestable"] is True for item in packets.values())
    assert all(item["opl_projection_only"] is True for item in packets.values())
    assert all(item["write_permitted"] is False for item in packets.values())
    assert all(item["domain_truth_owner"] == "med-autoscience" for item in packets.values())
    canary = evidence["real_paper_line_provider_canary_contract"]
    assert canary["gate_id"] == "real_paper_line_provider_canary"
    assert canary["task_id"] == "agent-lab-task:mas/real-paper-line-provider-canary"
    assert canary["success_criterion"] == "mas_owner_chain_returns_owner_receipt_or_stable_typed_blocker"
    assert canary["provider_completion_is_success"] is False
    assert canary["selected_opl_ingestable_ref_surface"] == (
        "product_entry_manifest.provider_guarded_soak_read_model.paper_line_guarded_apply_evidence"
    )
    assert canary["required_closeout_surface"] == "mas_real_paper_line_provider_canary_closeout"
    assert canary["allowed_terminal_owner_results"] == ["owner_receipt", "stable_typed_blocker"]
    assert "provider_or_opl_writes_current_package" in canary["forbidden_authority"]
    assert canary["body_included"] is False

    handoff = evidence["opl_stage_evidence_receipt_handoff"]
    assert handoff["surface_kind"] == "mas_opl_stage_evidence_receipt_handoff"
    assert handoff["mode"] == "refs_only_payload_hints"
    assert handoff["record_action"] == "stage_production_evidence_receipt_record"
    assert handoff["verify_action"] == "stage_production_evidence_receipt_verify"
    assert handoff["selected_mas_surface"] == "paper_line_guarded_apply_evidence"
    assert handoff["payload_body_included"] is False
    assert handoff["publication_ready_claimed"] is False
    assert handoff["current_package_update_claimed"] is False
    expected_hints = {item["hint_id"]: item for item in handoff["expected_receipt_ref_hints"]}
    assert set(expected_hints) == {
        "owner_receipt",
        "progress_delta",
        "ai_reviewer_gate_receipt",
        "artifact_movement",
        "human_gate_or_resume",
        "stable_typed_blocker",
        "no_forbidden_write_proof",
    }
    assert expected_hints["owner_receipt"]["source_ref_role"] == "owner_receipt_ref"
    assert expected_hints["no_forbidden_write_proof"]["source_packet_id"] == (
        "no_forbidden_write_proof_ref_packet"
    )
    assert all(item["record_role"] == "expected_receipt_ref" for item in expected_hints.values())
    assert all(item["body_included"] is False for item in expected_hints.values())
    freshness = {item["hint_id"]: item for item in handoff["monitor_freshness_ref_hints"]}
    assert set(freshness) == {
        "paper_progress_delta_freshness",
        "quality_gate_freshness",
        "artifact_movement_freshness",
        "human_gate_or_stable_blocker_freshness",
        "forbidden_write_guard_freshness",
    }
    assert freshness["forbidden_write_guard_freshness"]["source_ref_roles"] == [
        "no_forbidden_write_proof_ref"
    ]
    assert all(item["record_role"] == "monitor_freshness_ref" for item in freshness.values())
    assert handoff["closeout_requires"] == [
        "mas_owner_receipt_ref",
        "progress_delta_ref_or_stable_typed_blocker_ref",
        "no_forbidden_write_proof_ref",
    ]
    proof_handoff = evidence["no_forbidden_write_proof_handoff"]
    assert proof_handoff["proof_ref_role"] == "no_forbidden_write_proof_ref"
    assert proof_handoff["must_be_recorded_with_each_opl_stage_evidence_receipt"] is True
    assert proof_handoff["body_included"] is False
    assert proof_handoff["write_permitted"] is False
    assert proof_handoff["opl_projection_only"] is True


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
    assert payload["authority_boundary"]["domain_ready_requires_owner_receipt_or_typed_blocker"] is True
    assert payload["authority_boundary"]["quality_or_export_ready_requires_target_owner_gate"] is True
    assert payload["authority_boundary"]["artifact_mutation_requires_owner_receipt"] is True
    assert payload["authority_boundary"]["opl_can_write_memory_body"] is False
    assert payload["authority_boundary"]["opl_can_write_current_package"] is False


def test_agent_lab_handoff_is_connected_to_production_acceptance() -> None:
    payload = _acceptance()
    handoff = payload["agent_lab_handoff"]

    assert handoff["handoff_status"] == "ready_for_opl_meta_agent_and_agent_lab_execution"
    assert handoff["handoff_ref"] == {
        "ref": "contracts/agent_lab_handoff.json",
        "role": "domain_agent_lab_production_evidence_handoff",
        "body_included": False,
    }
    assert handoff["suite_kind"] == "agent_production_evidence_suite"
    assert handoff["target_consumers"] == ["one-person-lab.agent_lab", "opl-meta-agent"]
    assert handoff["target_opl_cli"] == "opl agent-lab run --suite <suite.json> --json"
    assert handoff["domain_verdict_claimed"] is False
    assert handoff["closeout_requires_domain_owner_receipt_or_typed_blocker"] is True
    assert handoff["required_gate_ids"] == [
        "real_paper_line_provider_canary",
        "memory_artifact_human_gate_scaleout",
        "provider_slo_long_soak",
    ]
    assert handoff["lane_4a_evidence_scaleout_ref"] == {
        "ref": "contracts/production_acceptance/mas-production-acceptance.json#/paper_line_guarded_apply_evidence",
        "role": "selected_existing_mas_evidence_surface",
        "body_included": False,
    }


def test_production_acceptance_exposes_same_oma_agent_evidence_refs() -> None:
    payload = _acceptance()
    oma = payload["oma_agent_evidence_refs"]

    assert oma["consumer_id"] == "opl-meta-agent.agent:evidence"
    assert oma["production_acceptance_ref"]["ref"] == (
        "contracts/production_acceptance/mas-production-acceptance.json"
    )
    assert oma["agent_lab_handoff_ref"]["ref"] == "contracts/agent_lab_handoff.json"
    assert oma["generated_surface_handoff_ref"]["ref"] == "contracts/generated_surface_handoff.json"
    assert {item["role"] for item in oma["authority_refs"]} == {
        "mas_owner_receipt_authority",
        "mas_quality_publication_authority",
        "mas_artifact_authority_locator",
        "mas_memory_authority_locator",
    }
    assert {
        item["ref"]
        for item in oma["editable_surface_hints"]
    } >= {
        "agent/prompts",
        "agent/skills",
        "agent/knowledge",
        "agent/quality_gates",
        "contracts/generated_surface_handoff.json",
        "contracts/agent_lab_handoff.json",
    }
    assert oma["consumer_policy"]["oma_may_consume_refs"] is True
    assert oma["consumer_policy"]["oma_may_emit_candidate_patch_work_order"] is True
    assert oma["consumer_policy"]["oma_may_sign_owner_receipt"] is False
    assert oma["consumer_policy"]["oma_may_write_quality_verdict"] is False
    assert oma["consumer_policy"]["oma_may_write_artifact_body"] is False
    assert oma["consumer_policy"]["oma_may_write_memory_body"] is False


def test_agent_lab_handoff_contract_declares_refs_only_consumers_and_suite_seed() -> None:
    handoff = _agent_lab_handoff()

    assert handoff["surface_kind"] == "domain_agent_lab_production_evidence_handoff"
    assert handoff["domain_id"] == "med-autoscience"
    assert handoff["owner"] == "MedAutoScience"
    assert handoff["handoff_status"] == "ready_for_opl_meta_agent_and_agent_lab_execution"

    consumers = {consumer["consumer_id"]: consumer for consumer in handoff["target_consumers"]}
    assert set(consumers) == {"one-person-lab.agent_lab", "opl-meta-agent"}
    assert "run_external_suite" in consumers["one-person-lab.agent_lab"]["allowed_actions"]
    assert "materialize_external_suite" in consumers["opl-meta-agent"]["allowed_actions"]
    for consumer in consumers.values():
        assert {"domain_truth_write", "publication_quality_verdict", "artifact_body_write", "memory_body_write"} <= set(
            consumer["forbidden_authority"]
        )

    suite = handoff["external_suite_seed"]
    assert suite["suite_id"] == "mas-production-evidence-tail-suite"
    assert suite["suite_kind"] == "agent_production_evidence_suite"
    assert suite["domain_verdict_claimed"] is False
    assert suite["lane_4a_selected_evidence_surface"] == {
        "ref": "contracts/production_acceptance/mas-production-acceptance.json#/paper_line_guarded_apply_evidence",
        "role": "selected_existing_mas_evidence_surface",
        "body_included": False,
    }
    assert suite["opl_stage_evidence_receipt_handoff_ref"] == {
        "ref": "contracts/production_acceptance/mas-production-acceptance.json#/paper_line_guarded_apply_evidence/opl_stage_evidence_receipt_handoff",
        "role": "opl_expected_receipt_and_monitor_freshness_payload_hints",
        "body_included": False,
    }
    assert suite["required_task_ids"] == [
        "agent-lab-task:mas/real-paper-line-provider-canary",
        "agent-lab-task:mas/memory-artifact-human-gate-scaleout",
        "agent-lab-task:mas/provider-slo-long-soak",
    ]


def test_agent_lab_handoff_exposes_oma_agent_evidence_refs_without_authority_transfer() -> None:
    handoff = _agent_lab_handoff()
    oma = handoff["oma_agent_evidence_refs"]

    assert oma["consumer_id"] == "opl-meta-agent.agent:evidence"
    assert oma["production_acceptance_ref"] == {
        "ref": "contracts/production_acceptance/mas-production-acceptance.json",
        "role": "mas_domain_owned_production_acceptance",
        "body_included": False,
    }
    assert oma["agent_lab_handoff_ref"] == {
        "ref": "contracts/agent_lab_handoff.json",
        "role": "domain_agent_lab_production_evidence_handoff",
        "body_included": False,
    }
    assert oma["generated_surface_handoff_ref"] == {
        "ref": "contracts/generated_surface_handoff.json",
        "role": "opl_generated_surface_handoff",
        "body_included": False,
    }

    authority_refs = {item["role"]: item for item in oma["authority_refs"]}
    assert set(authority_refs) == {
        "mas_owner_receipt_authority",
        "mas_quality_publication_authority",
        "mas_artifact_authority_locator",
        "mas_memory_authority_locator",
    }
    assert authority_refs["mas_owner_receipt_authority"]["ref"] == "contracts/owner_receipt_contract.json"
    assert authority_refs["mas_quality_publication_authority"]["ref"] == "publication_eval/latest.json"
    assert authority_refs["mas_artifact_authority_locator"]["ref"] == "contracts/artifact_locator_contract.json"
    assert authority_refs["mas_memory_authority_locator"]["ref"] == "contracts/memory_descriptor.json"
    assert all(item["body_included"] is False for item in authority_refs.values())

    editable_refs = {item["ref"] for item in oma["editable_surface_hints"]}
    assert editable_refs >= {
        "agent/prompts",
        "agent/skills",
        "agent/knowledge",
        "agent/quality_gates",
        "contracts/generated_surface_handoff.json",
        "contracts/agent_lab_handoff.json",
        "contracts/production_acceptance/mas-production-acceptance.json",
    }
    assert all(item["body_included"] is False for item in oma["editable_surface_hints"])
    assert oma["consumer_policy"] == {
        "oma_may_consume_refs": True,
        "oma_may_emit_candidate_patch_work_order": True,
        "oma_may_sign_owner_receipt": False,
        "oma_may_write_quality_verdict": False,
        "oma_may_write_artifact_body": False,
        "oma_may_write_memory_body": False,
    }


def test_agent_lab_handoff_tasks_keep_domain_receipts_as_closeout_authority() -> None:
    handoff = _agent_lab_handoff()
    suite = handoff["external_suite_seed"]
    tasks = {task["gate_id"]: task for task in suite["tasks"]}

    assert set(tasks) == {
        "real_paper_line_provider_canary",
        "memory_artifact_human_gate_scaleout",
        "provider_slo_long_soak",
    }
    assert tasks["real_paper_line_provider_canary"]["owner_route"] == "MedAutoScience"
    assert "owner_receipt" in tasks["real_paper_line_provider_canary"]["required_return_shapes"]
    assert "no_forbidden_write_proof_ref" in tasks["real_paper_line_provider_canary"]["allowed_opl_result_refs"]
    assert {
        "owner_receipt_ref",
        "progress_delta_ref",
        "ai_reviewer_gate_receipt_ref",
        "artifact_movement_ref",
        "human_gate_or_resume_ref",
        "stable_typed_blocker_ref",
    } <= set(tasks["real_paper_line_provider_canary"]["allowed_opl_result_refs"])
    assert {
        "artifact_movement_ref",
        "human_gate_or_resume_ref",
    } <= set(tasks["memory_artifact_human_gate_scaleout"]["allowed_opl_result_refs"])
    assert "agent_lab_result_authorizes_domain_ready" in tasks["real_paper_line_provider_canary"][
        "forbidden_claims"
    ]

    closeout = handoff["receipt_closeout_policy"]
    assert closeout["agent_lab_result_is_evidence_not_domain_verdict"] is True
    assert closeout["meta_agent_work_order_is_candidate_not_domain_verdict"] is True
    assert closeout["closeout_requires_domain_owner_receipt_or_typed_blocker"] is True
    assert closeout["publication_ready_requires_independent_domain_reviewer_or_auditor_gate"] is True
    assert closeout["artifact_mutation_requires_domain_artifact_authority_receipt"] is True
    assert closeout["memory_accept_reject_requires_domain_memory_receipt"] is True
    assert closeout["lane_4a_scaleout_closeout_requires"] == [
        "mas_owner_receipt_ref",
        "progress_delta_ref",
        "ai_reviewer_gate_receipt_ref",
        "artifact_movement_ref",
        "human_gate_or_resume_ref",
        "stable_typed_blocker_ref",
        "no_forbidden_write_proof_ref",
    ]


def test_agent_lab_handoff_work_order_has_traceability_and_forbidden_write_proof() -> None:
    handoff = _agent_lab_handoff()
    work_order = handoff["meta_agent_work_order_contract"]

    assert work_order["target_script_ref"] == (
        "npm run agent:evidence -- --agent-repo <agent_repo> --output-dir <dir> --opl-bin <opl>"
    )
    assert "contracts/agent_lab_handoff.json" in work_order["editable_surface_refs"]
    assert "default_agent_promotion" in work_order["forbidden_target_writes"]
    assert set(work_order["required_output_refs"]) == {
        "agent-lab-suite.json",
        "agent-lab-run-result.json",
        "developer-patch-work-order.json",
        "opl-stage-evidence-receipt-workorder.json",
        "target-capability-improvement-candidate.json",
        "mechanism-patch-proposal.json",
        "no-forbidden-write-proof.json",
    }
    assert set(work_order["required_traceability_axes"]) == {
        "source_gate_id",
        "source_task_id",
        "required_patch_refs",
        "editable_surface_refs",
        "verification_command_refs",
        "owner_route",
        "forbidden_write_proof_ref",
        "expected_receipt_ref",
        "monitor_freshness_ref",
    }
