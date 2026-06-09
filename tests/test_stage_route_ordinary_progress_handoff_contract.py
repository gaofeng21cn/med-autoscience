from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]


def _route_contract() -> dict[str, object]:
    return yaml.safe_load(
        (REPO_ROOT / "agent/stages/stage_route_contract.yaml").read_text(encoding="utf-8")
    )


def _kernel_handoff() -> dict[str, object]:
    return json.loads(
        (REPO_ROOT / "contracts/stage_run_kernel_profile.json").read_text(encoding="utf-8")
    )["ordinary_progress_handoff"]


def test_stage_route_contract_declares_ordinary_progress_handoff_policy() -> None:
    policy = _route_contract()["ordinary_progress_handoff_policy"]
    kernel_handoff = _kernel_handoff()

    assert policy["source_ref"] == "contracts/stage_run_kernel_profile.json#/ordinary_progress_handoff"
    assert policy["default_progress_root"] == "current_owner_delta"
    assert policy["stage_goal_source"] == "stage_run_current_owner_delta"
    assert policy["executor_output_requirement"] == "concrete_delta"
    assert policy["accepted_closeout_shapes"] == [
        "ProgressDeltaReceipt",
        "OwnerReceipt",
        "TypedBlocker",
        "human_gate_ref",
        "route_back_ref",
    ]

    progress_receipt = policy["progress_delta_receipt"]
    assert progress_receipt["receipt_kind"] == "ProgressDeltaReceipt"
    assert progress_receipt["artifact_tier"] == "T0_progress_delta"
    assert {
        "changed_surface_refs",
        "produced_refs",
        "consumed_refs",
        "progress_delta_classification",
        "deliverable_progress_delta",
        "platform_repair_delta",
        "next_owner",
        "next_required_delta",
    } <= set(progress_receipt["required_fields"])
    assert {
        "publication_ready",
        "submission_ready",
        "artifact_authority",
        "production_ready",
        "physical_delete",
    } <= set(progress_receipt["cannot_authorize"])

    assert policy["artifact_tier_policy"]["default_tier"] == "T0_progress_delta"
    assert policy["artifact_tier_policy"]["ordinary_delta_requires_full_stage_artifact_manifest"] is False
    assert policy["readiness_jit_policy"]["default_mode"] == "just_in_time_for_current_delta"
    assert (
        policy["readiness_jit_policy"][
            "cannot_require_all_surfaces_before_writing_analysis_or_review_delta"
        ]
        is True
    )
    assert policy["audit_sidecar_policy"]["can_generate_default_next_action"] is False
    assert policy["audit_sidecar_policy"]["can_close_stage"] is False
    assert policy["audit_sidecar_policy"]["can_claim_domain_ready"] is False

    canary = policy["owner_chain_canary_proof"]
    assert canary == kernel_handoff["owner_chain_canary_proof"]
    assert canary["canary_surface"] == "paper_line_owner_chain_results"
    assert canary["per_paper_line_required_fields"] == [
        "ordinary_progress_handoff_proof",
        "accepted_closeout_shape",
        "ProgressDeltaReceipt_or_OwnerReceipt_or_TypedBlocker",
        "next_owner",
        "next_required_delta",
        "readiness_jit_scope",
        "audit_sidecar_passive",
    ]
    assert canary["accepted_terminal_shapes"] == ["OwnerReceipt", "TypedBlocker"]
    assert canary["provider_completion_can_close"] is False
    assert canary["readiness_inventory_can_generate_default_next_action"] is False
    assert canary["audit_sidecar_can_generate_default_next_action"] is False
    assert canary["success_path_requires_owner_receipt_or_stable_typed_blocker"] is True
