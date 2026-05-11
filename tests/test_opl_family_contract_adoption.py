from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = "contracts/opl-framework/family-contract-adoption.json"


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _contract() -> dict[str, object]:
    return json.loads(_read(CONTRACT_PATH))


def test_mas_declares_thin_opl_family_contract_adoption() -> None:
    contract = _contract()

    assert contract["contract_kind"] == "mas_opl_family_contract_adoption.v1"
    assert contract["domain_id"] == "med-autoscience"
    assert contract["opl_role"] == (
        "Codex-first stage-led provider-backed runtime framework and family-level projection consumer"
    )
    framework = contract["opl_framework_contract"]
    assert framework["owner"] == "one-person-lab"
    assert framework["framework_role"] == "codex_first_stage_led_provider_backed_runtime_framework"
    assert framework["stage_semantics"] == "human_expert_large_task_stage"
    assert framework["minimal_executor"] == "Codex CLI"
    assert framework["provider_abstraction"] == "opl_family_runtime_provider"
    assert framework["target_production_provider"] == "Temporal"
    assert framework["legacy_optional_providers"] == ["Hermes-Agent"]
    assert set(framework["allowed_framework_authority"]) == {
        "stage_attempt",
        "queue",
        "wakeup",
        "retry",
        "dead_letter",
        "human_gate_signal",
        "attempt_receipt",
        "projection",
        "cross_domain_skeleton",
    }
    assert set(framework["forbidden_framework_authority"]) == {
        "study_truth",
        "publication_quality",
        "quality_gate",
        "artifact_authority",
        "paper_package",
    }


def test_mas_runtime_projection_maps_to_existing_runtime_truth_surfaces() -> None:
    contract = _contract()
    attempt = contract["attempt_projection"]

    for surface in ("study_runtime_status", "runtime_watch", "controller_decisions/latest.json"):
        assert surface in attempt["source_surfaces"]
    assert attempt["maps_to_opl_contract"] == "opl_family_runtime_attempt_contract.v1"
    assert "study runtime truth" in attempt["owner_boundary"]


def test_mas_quality_projection_keeps_medical_quality_owner_and_blocks_claim_only_ready() -> None:
    contract = _contract()
    quality = contract["quality_projection"]

    for surface in (
        "study_charter",
        "evidence_ledger",
        "review_ledger",
        "publication_eval/latest.json",
    ):
        assert surface in quality["source_surfaces"]
    assert quality["maps_to_opl_contract"] == "opl_family_domain_quality_projection_contract.v1"
    assert quality["claim_only_ready_forbidden"] is True


def test_mas_operator_and_incident_projection_require_source_refs_and_mas_closure() -> None:
    contract = _contract()
    incident = contract["incident_projection"]
    operator = contract["operator_projection"]

    assert incident["maps_to_opl_contract"] == "opl_family_incident_learning_loop.v1"
    assert "MAS-owned closure ref" in incident["closure_rule"]
    assert "ai_doctor_request" in incident["ai_doctor_boundary"]
    for surface in (
        "artifacts/autonomy/slo_status/latest.json",
        "artifacts/autonomy/ai_doctor_requests/*.json",
        "artifacts/autonomy/ai_doctor_diagnoses/*.json",
        "artifacts/autonomy/repair_actions/*.json",
    ):
        assert surface in incident["source_surfaces"]
    for field in (
        "source_refs",
        "freshness",
        "owner_split",
        "next_surface_ref",
        "human_gate_reason",
        "autonomy_slo",
        "ai_doctor_state",
        "repair_recommendation",
    ):
        assert field in operator["required_fields"]
    for non_goal in contract["non_goals"]:
        assert non_goal not in ("", None)


def test_mas_persistence_lifecycle_owner_route_projection_is_refs_payload_only() -> None:
    contract = _contract()
    projection = contract["persistence_lifecycle_owner_route_projection"]

    assert projection["adoption_surface_kind"] == (
        "mas_opl_family_persistence_lifecycle_owner_route_adoption"
    )
    assert projection["required_shape"] == ["refs", "payload"]
    assert projection["maps_to_opl_contracts"] == {
        "persistence": "opl_family_persistence_contract.v1",
        "lifecycle": "opl_family_lifecycle_contract.v1",
        "owner_route": "opl_family_owner_route_contract.v1",
    }
    assert "artifacts/runtime/runtime_lifecycle.sqlite" in projection["source_surfaces"]
    assert "owner_route_receipts" in projection["sqlite_tables"]
    assert "surface_refs" in projection["sqlite_tables"]
    assert projection["authority_boundary"] == (
        "OPL may discover and index MAS refs/payload; MAS keeps study, publication, AI reviewer, and paper package authority"
    )
    assert projection["forbidden_opl_authority_surfaces"] == [
        "publication_eval/latest.json",
        "AI reviewer workflow",
        "paper/manuscript/current_package",
        "current_package.zip",
    ]


def test_mas_domain_memory_projection_declares_domain_owned_migration_surface() -> None:
    contract = _contract()
    memory = contract["domain_memory_projection"]

    assert memory["descriptor_surface"] == "product-entry-manifest.domain_memory_descriptor"
    assert memory["memory_ref_id"] == "mas_publication_route_memory"
    assert memory["migration_plan_ref"] == (
        "docs/policies/study-workflow/publication_route_memory_policy.md#migration-plan"
    )
    assert memory["seed_corpus_ref"] == (
        "docs/policies/study-workflow/publication_route_memory_seed_fixture.json"
    )
    assert memory["writeback_receipt_locator_ref"] == (
        "portfolio/research_memory/publication_route_memory/writeback_receipts"
    )
    assert memory["workspace_apply_surface"] == {
        "seed_apply_receipt_surface": "publication_route_memory_apply_receipt",
        "memory_pack_surface": "publication_route_memory_pack",
        "memory_pack_locator": "portfolio/research_memory/publication_route_memory/memory_pack.json",
        "migration_receipt_locator": "portfolio/research_memory/publication_route_memory/migration_receipts",
        "repo_tracks_real_pack_or_receipts": False,
    }
    assert memory["migration_readiness"] == {
        "status": "workspace_apply_closure_ready",
        "seed_fixture_status": "repo_source_fixture_available",
        "memory_body_migration": "domain_owned_workspace_apply_available",
        "opl_apply_allowed": False,
    }
    assert "memory_store_owner" in memory["forbidden_opl_authority"]
    assert "publication_route_decision_owner" in memory["forbidden_opl_authority"]
