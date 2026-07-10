from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta
REPO_ROOT = Path(__file__).resolve().parents[1]


def test_mas_foundry_agent_os_kernel_manifest_preserves_authority_boundary() -> None:
    manifest = json.loads(
        (REPO_ROOT / "contracts/foundry-agent-os-domain-kernel-manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["domain_agent_id"] == "mas"
    assert manifest["owner"] == "MedAutoScience"
    kernel = manifest["domain_authority_kernel"]
    assert {
        "medical_research_truth",
        "study_truth",
        "source_and_data_readiness_verdict",
        "ai_reviewer_or_auditor_quality_verdict",
        "publication_gate",
        "artifact_mutation_authorization",
        "publication_route_memory_accept_reject_or_blocker",
        "owner_receipt_signer", "typed_blocker_materializer", "domain_native_helper_guard",
    } == set(kernel["retained_surfaces"])
    assert (
        kernel["retained_surface_owner"], kernel["owner_receipt_signer"], kernel["typed_blocker_signer"]
    ) == ("med-autoscience", "med-autoscience_authority_kernel", "med-autoscience_authority_kernel")
    assert {
        "mas_owner_receipt_ref", "mas_typed_blocker_ref",
        "quality_gate_receipt_ref", "publication_gate_receipt_ref",
        "human_gate_ref", "route_back_evidence_ref", "no_regression_evidence_ref",
    } == set(kernel["accepted_answer_shapes"])
    assert manifest["default_read_root"] == {
        "surface": "current_owner_delta", "ordinary_operator_root": True,
        "raw_worklist_role": "drilldown_only", "provider_completion_role": "transport_evidence_only",
        "evidence_count_role": "audit_only", "projection_can_be_owner_answer": False,
    }
    assert {
        "generic_runtime", "stage_run_kernel",
        "queue_and_attempt_ledger", "retry_dead_letter_resume",
        "human_gate_transport", "state_index_kernel",
        "workspace_source_shell", "artifact_memory_lifecycle_shell",
        "generated_cli_mcp_skill_product_workbench_surfaces", "console_current_owner_delta_projection",
        "refs_only_vault_lineage", "capability_registry_abi",
    } == set(manifest["opl_upcollect_surfaces"])
    flags = manifest["forbidden_authority_flags"]
    assert set(flags) == {"opl", "vault", "console", "runway", "pack", "capability_registry"}
    flag_names = {
        "can_write_domain_truth", "can_sign_owner_receipt", "can_create_domain_typed_blocker",
        "can_authorize_quality_export_publication_or_review_verdict",
    }
    assert all(value == dict.fromkeys(flag_names, False) for value in flags.values())
    assert manifest["non_claims"] == dict.fromkeys({
        "domain_ready", "publication_ready", "submission_ready", "production_ready",
        "app_release_ready", "physical_delete_authorized",
    }, False)
