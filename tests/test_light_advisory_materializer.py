from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.light_advisory_materializer import (
    materialize_light_advisory_refs,
)


def _write(path: Path, text: str = "content\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_light_advisory_materializer_writes_consumable_refs_without_authority_claims(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    _write(study_root / "study.yaml", "study_id: 001-risk\n")
    _write(study_root / "paper" / "evidence_ledger.json", '{"claims": []}\n')

    result = materialize_light_advisory_refs(
        study_root=study_root,
        study_id="001-risk",
        work_unit_id="wu-review-001",
        owner_action="run_ai_reviewer_workflow",
        stage="review",
        source_refs=("study.yaml", "paper/evidence_ledger.json"),
        payload={
            "collision_check": {
                "core_claim_ref": "paper/evidence_ledger.json#/claims/0",
                "nearest_neighbor_work_refs": ["pmid:neighbor-1"],
                "negative_search_evidence_refs": ["search:pubmed:2026-06-10"],
                "novelty_delta_ref": "paper/evidence_ledger.json#/novelty",
            },
            "refusal_rehearsal": {
                "top_refusal_reason_refs": ["review-risk:missing-external-validation"],
                "reviewer_position_ref": "reviewer:critical",
                "unresolved_critical_refs": [],
            },
            "fresh_evidence_gate": {
                "verification_command_or_ref": "scripts/verify.sh",
                "verification_exit_state": "passed",
                "evidence_refs": ["test:light-advisory-materializer"],
            },
            "next_owner_effect": "brief_next_reviewer_without_blocking_dispatch",
        },
        apply=True,
    )

    assert result["status"] == "materialized"
    assert result["typed_blocker"] is None
    assert result["missing_advisory_ref_kinds"] == []
    assert result["authority_boundary"] == {
        "refs_only": True,
        "can_write_study_truth": False,
        "can_write_artifact_body": False,
        "can_write_memory_body": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_source_readiness": False,
        "can_sign_owner_receipt": False,
        "can_admit_route": False,
    }
    assert all(ref["blocks_unrelated_owner_dispatch"] is False for ref in result["advisory_refs"])
    assert {ref["ref_kind"] for ref in result["advisory_refs"]} == {
        "verified_asset_ref",
        "collision_check_ref",
        "refusal_rehearsal_ref",
        "fresh_evidence_gate_ref",
    }

    bundle_path = study_root / result["bundle_ref"]
    assert bundle_path.is_file()
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert bundle["surface_kind"] == "light_external_advisory_ref_bundle"
    assert bundle["stage_id"] == "review"
    assert bundle["progress_first_policy"]["missing_advisory_behavior"] == "do_not_block_dispatch"
    assert bundle["light_runtime_dependency"] is False
    assert bundle["light_router_dependency"] is False
    assert bundle["light_db09_dependency"] is False
    assert not (bundle_path.parent.parent / "receipts" / "owner_receipt.json").exists()

    ref_root = bundle_path.parent / "refs"
    for ref_kind in ("verified_asset_ref", "collision_check_ref", "refusal_rehearsal_ref", "fresh_evidence_gate_ref"):
        ref_payload = json.loads((ref_root / f"{ref_kind}.json").read_text(encoding="utf-8"))
        assert ref_payload["ref_kind"] == ref_kind
        assert ref_payload["study_id"] == "001-risk"
        assert ref_payload["work_unit_id"] == "wu-review-001"
        assert ref_payload["owner_action"] == "run_ai_reviewer_workflow"
        assert ref_payload["light_runtime_dependency"] is False
        assert ref_payload["blocks_unrelated_owner_dispatch"] is False


def test_light_advisory_materializer_only_blocks_current_delta_for_route_required_hard_gate(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    _write(study_root / "study.yaml", "study_id: 001-risk\n")

    result = materialize_light_advisory_refs(
        study_root=study_root,
        study_id="001-risk",
        work_unit_id="wu-write-001",
        owner_action="write_claim_supported_paragraph",
        stage="write",
        source_refs=("study.yaml",),
        payload={
            "fresh_evidence_gate": {
                "verification_command_or_ref": "scripts/verify.sh",
                "verification_exit_state": "passed",
            },
        },
        route_required_ref_kinds=("citation_locator_audit_ref",),
        hard_gate=True,
        apply=True,
    )

    assert result["status"] == "typed_blocker_candidate"
    assert result["missing_advisory_ref_kinds"] == [
        "collision_check_ref",
        "refusal_rehearsal_ref",
        "citation_locator_audit_ref",
    ]
    assert result["typed_blocker"] is None
    assert result["typed_blocker_candidate"] == {
        "surface_kind": "light_external_advisory_typed_blocker_candidate",
        "schema_version": 1,
        "candidate_id": result["typed_blocker_candidate"]["candidate_id"],
        "candidate_type": "light_advisory_route_required_ref_missing",
        "study_id": "001-risk",
        "work_unit_id": "wu-write-001",
        "owner_action": "write_claim_supported_paragraph",
        "stage": "write",
        "missing_ref_kinds": ["citation_locator_audit_ref"],
        "recorded_at": result["typed_blocker_candidate"]["recorded_at"],
        "may_block_current_delta_after_owner_materialization": True,
        "blocks_unrelated_owner_dispatch": False,
        "hard_gate_candidate_requires_owner_or_reviewer_materialization": True,
        "resolution_owner": "write_claim_supported_paragraph",
        "light_runtime_dependency": False,
        "authority_boundary": result["authority_boundary"],
    }
    candidate_path = study_root / result["typed_blocker_candidate_ref"]
    assert candidate_path.is_file()
    assert result["typed_blocker_ref"] is None


def test_light_advisory_materializer_keeps_missing_advisory_non_blocking_without_hard_gate(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    _write(study_root / "study.yaml", "study_id: 001-risk\n")

    result = materialize_light_advisory_refs(
        study_root=study_root,
        work_unit_id="wu-scout-001",
        owner_action="scout_next_delta",
        source_refs=("study.yaml",),
        route_required_ref_kinds=("collision_check_ref",),
        hard_gate=False,
        apply=False,
    )

    assert result["status"] == "dry_run"
    assert "collision_check_ref" in result["missing_advisory_ref_kinds"]
    assert result["typed_blocker"] is None
    assert result["typed_blocker_ref"] is None
    assert result["progress_first_policy"]["route_required_missing_without_hard_gate"] == (
        "advisory_gap_only"
    )
    assert not (study_root / result["bundle_ref"]).exists()


def test_light_advisory_materializer_writes_optional_skill_content_refs_only_when_payload_present(
    tmp_path: Path,
) -> None:
    study_root = tmp_path / "studies" / "001-risk"
    _write(study_root / "study.yaml", "study_id: 001-risk\n")
    _write(study_root / "paper" / "evidence_ledger.json", '{"claims": []}\n')

    result = materialize_light_advisory_refs(
        study_root=study_root,
        study_id="001-risk",
        work_unit_id="wu-write-review-001",
        owner_action="repair_claim_evidence_and_display_refs",
        stage="write",
        source_refs=("study.yaml", "paper/evidence_ledger.json"),
        payload={
            "citation_locator_audit": {
                "claim_segment_id": "claim-1",
                "citation_ref": "pmid:123",
                "locator_ref": "pmid:123#table-2",
                "support_state": "partial",
                "rewrite_or_replace_ref": "paper/evidence_ledger.json#/claims/0/repair",
            },
            "prisma_flow_reconciliation": {
                "search_source_count_refs": ["pubmed:query-1"],
                "dedup_count_ref": "screening:dedup",
                "included_study_count_ref": "screening:included",
                "count_reconciled": True,
            },
            "argument_review_hint": {
                "claim_ref": "paper/evidence_ledger.json#/claims/0",
                "evidence_ref": "paper/evidence_ledger.json#/evidence/0",
                "boundary_ref": "paper/evidence_ledger.json#/claims/0/boundary",
                "claim_boundary_state": "downgrade_required",
            },
            "figure_integrity_warning": {
                "figure_ref": "figures/fig1.pdf",
                "warnings": [
                    {"warning_ref": "axis:truncated", "caption_disclosure_ref": "caption:fig1"}
                ],
            },
            "style_fingerprint_hint": {
                "reference_style_profile_ref": "memory:approved-style",
                "draft_style_profile_ref": "manuscript:current-draft",
                "deviation_hint_ref": "style:terminology-drift",
            },
        },
        apply=True,
    )

    assert result["status"] == "materialized"
    assert result["typed_blocker"] is None
    ref_kinds = {ref["ref_kind"] for ref in result["advisory_refs"]}
    assert {
        "verified_asset_ref",
        "citation_locator_audit_ref",
        "prisma_flow_reconciliation_ref",
        "argument_review_hint_ref",
        "figure_integrity_warning_ref",
        "style_fingerprint_hint_ref",
    } <= ref_kinds
    assert "citation_locator_audit_ref" not in result["missing_advisory_ref_kinds"]
    assert result["missing_advisory_ref_kinds"] == [
        "collision_check_ref",
        "refusal_rehearsal_ref",
        "fresh_evidence_gate_ref",
    ]

    refs_by_kind = {ref["ref_kind"]: ref for ref in result["advisory_refs"]}
    assert refs_by_kind["citation_locator_audit_ref"]["support_state"] == "partial"
    assert refs_by_kind["prisma_flow_reconciliation_ref"]["count_reconciled"] is True
    assert refs_by_kind["prisma_flow_reconciliation_ref"]["systematic_review_only"] is True
    assert refs_by_kind["argument_review_hint_ref"]["claim_boundary_state"] == "downgrade_required"
    assert refs_by_kind["figure_integrity_warning_ref"]["warning_count"] == 1
    assert refs_by_kind["figure_integrity_warning_ref"]["artifact_mutation_authority"] is False
    assert refs_by_kind["style_fingerprint_hint_ref"]["watch_only"] is True
    assert (
        refs_by_kind["style_fingerprint_hint_ref"]["may_override_evidence_or_reviewer_concerns"]
        is False
    )

    bundle_path = study_root / result["bundle_ref"]
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    assert {
        "citation_locator_audit_ref",
        "prisma_flow_reconciliation_ref",
        "argument_review_hint_ref",
        "figure_integrity_warning_ref",
        "style_fingerprint_hint_ref",
    } <= set(bundle["advisory_ref_paths"])
    assert not (bundle_path.parent.parent / "receipts" / "owner_receipt.json").exists()
