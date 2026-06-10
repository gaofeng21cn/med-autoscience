from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]


def _manifest() -> dict[str, object]:
    return json.loads(
        (REPO_ROOT / "contracts/foundry-agent-os-domain-kernel-manifest.json").read_text(
            encoding="utf-8"
        )
    )


def test_mas_foundry_agent_os_kernel_manifest_declares_domain_authority() -> None:
    manifest = _manifest()

    assert manifest["surface_kind"] == "foundry_agent_os_domain_kernel_manifest"
    assert manifest["domain_id"] == "med-autoscience"
    assert manifest["domain_agent_id"] == "mas"
    assert manifest["owner"] == "MedAutoScience"
    assert manifest["role"] == "w4_domain_kernel_manifest"

    kernel = manifest["domain_authority_kernel"]
    retained = set(kernel["retained_surfaces"])
    assert {
        "medical_research_truth",
        "study_truth",
        "source_and_data_readiness_verdict",
        "ai_reviewer_or_auditor_quality_verdict",
        "publication_gate",
        "artifact_mutation_authorization",
        "publication_route_memory_accept_reject_or_blocker",
        "owner_receipt_signer",
        "typed_blocker_materializer",
    } <= retained
    assert kernel["owner_receipt_signer"] == "med-autoscience_authority_kernel"
    assert kernel["typed_blocker_signer"] == "med-autoscience_authority_kernel"
    assert "publication_gate" in kernel["quality_export_publication_review_verdict_signers"]
    assert "mas_owner_receipt_ref" in kernel["accepted_answer_shapes"]
    assert "mas_typed_blocker_ref" in kernel["accepted_answer_shapes"]


def test_mas_foundry_agent_os_kernel_manifest_upcollects_generic_surfaces_to_opl() -> None:
    manifest = _manifest()

    assert manifest["default_read_root"] == {
        "surface": "current_owner_delta",
        "ordinary_operator_root": True,
        "raw_worklist_role": "drilldown_only",
        "provider_completion_role": "transport_evidence_only",
        "evidence_count_role": "audit_only",
        "projection_can_be_owner_answer": False,
    }
    assert set(manifest["opl_upcollect_surfaces"]) >= {
        "generic_runtime",
        "stage_run_kernel",
        "queue_and_attempt_ledger",
        "workspace_source_shell",
        "artifact_memory_lifecycle_shell",
        "generated_cli_mcp_skill_product_workbench_surfaces",
        "console_current_owner_delta_projection",
        "refs_only_vault_lineage",
        "capability_registry_abi",
    }


def test_mas_foundry_agent_os_kernel_manifest_forbids_false_authority() -> None:
    manifest = _manifest()

    for surface in ["opl", "vault", "console", "runway", "pack", "capability_registry"]:
        flags = manifest["forbidden_authority_flags"][surface]
        assert flags["can_write_domain_truth"] is False
        assert flags["can_sign_owner_receipt"] is False
        assert flags["can_create_domain_typed_blocker"] is False
        assert flags["can_authorize_quality_export_publication_or_review_verdict"] is False

    assert manifest["non_claims"] == {
        "domain_ready": False,
        "publication_ready": False,
        "submission_ready": False,
        "production_ready": False,
        "app_release_ready": False,
        "physical_delete_authorized": False,
    }
