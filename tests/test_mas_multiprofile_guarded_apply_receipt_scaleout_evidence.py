from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = (
    REPO_ROOT
    / "contracts"
    / "production_acceptance"
    / "mas-multiprofile-guarded-apply-receipt-scaleout-evidence-20260527.json"
)


def _snapshot() -> dict[str, object]:
    return json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))


def _walk_dicts(value: object):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_dicts(child)


def test_multiprofile_guarded_apply_snapshot_records_unique_cross_profile_lines() -> None:
    payload = _snapshot()

    assert payload["surface_kind"] == "mas_multiprofile_guarded_apply_receipt_scaleout_evidence"
    assert payload["evidence_id"] == "mas-multiprofile-guarded-apply-receipt-scaleout-20260527"
    assert payload["snapshot_status"] == "refs_only_multiprofile_owner_chain_snapshot_observed"
    assert payload["opl_ingestable_surface"] == (
        "product_entry_manifest.provider_guarded_soak_read_model.paper_line_guarded_apply_evidence"
    )
    assert payload["selected_acceptance_surface"] == {
        "ref": "contracts/production_acceptance/mas-production-acceptance.json#/paper_line_guarded_apply_evidence",
        "role": "selected_existing_mas_evidence_surface",
        "body_included": False,
    }

    expected_lines = [
        "001-dm-cvd-mortality-risk",
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
        "004-dpcc-longitudinal-care-inertia-intensification-gap",
        "001-lineage-pfs",
        "002-early-residual-risk",
        "003-endocrine-burden-followup",
        "004-invasive-architecture",
        "obesity_multicenter_phenotype_atlas",
    ]
    assert payload["paper_line_identity_order"] == expected_lines
    assert [item["paper_line_id"] for item in payload["paper_line_owner_chain_results"]] == expected_lines
    assert [item["study_id"] for item in payload["domain_dispatch_payload_summaries"]] == expected_lines


def test_multiprofile_guarded_apply_snapshot_preserves_success_and_blocker_counts() -> None:
    payload = _snapshot()

    assert payload["live_summary"] == {
        "target_study_count": 9,
        "guarded_receipt_count": 9,
        "typed_blocker_count": 5,
        "mas_owner_apply_receipt_count": 4,
        "artifact_delta_or_gate_progress_count": 2,
        "memory_final_proof_status": "final_ref_chain_proven",
        "forbidden_write_guard_result": "fail_closed_no_forbidden_writes",
        "writes_performed": True,
        "real_workspace_mutation_allowed": True,
        "guarded_apply_performed": True,
        "mas_owner_receipt_observed": True,
    }
    assert payload["paper_line_owner_payload_summary"] == {
        "paper_line_count": 9,
        "success_payload_count": 4,
        "typed_blocker_payload_count": 5,
        "domain_ready_claim_count": 0,
        "production_ready_claim_count": 0,
        "artifact_mutation_authorized_count": 0,
    }
    stage_summary = payload["stage_expected_receipt_payload_summary"]
    assert stage_summary["surface_kind"] == "mas_stage_expected_receipt_payload_summary"
    assert stage_summary["owner"] == "med-autoscience"
    assert stage_summary["consumer"] == "one_person_lab"
    assert stage_summary["status"] == (
        "per_stage_expected_receipt_payload_refs_ready_with_live_evidence_typed_blockers"
    )
    assert stage_summary["payload_body_allowed"] is False
    assert stage_summary["empty_payload_template_is_success_evidence"] is False
    assert stage_summary["body_included"] is False
    assert stage_summary["summary_source_surface"] == "domain_dispatch_payload_summaries"
    assert stage_summary["paper_line_count"] == 9
    assert stage_summary["success_payload_count"] == 4
    assert stage_summary["typed_blocker_payload_count"] == 5
    assert stage_summary["domain_ready_claim_count"] == 0
    assert stage_summary["production_ready_claim_count"] == 0
    assert stage_summary["publication_ready_claim_count"] == 0
    assert stage_summary["artifact_mutation_authorized_count"] == 0
    assert stage_summary["current_package_mutation_authorized_count"] == 0
    assert stage_summary["required_operator_payload_refs"] == [
        "domain_receipt_refs",
        "monitor_freshness_refs",
        "runtime_event_refs",
        "typed_blocker_refs",
    ]
    assert stage_summary["required_return_shapes"] == [
        "domain_receipt_ref",
        "monitor_freshness_ref",
        "runtime_event_ref",
        "typed_blocker_ref",
    ]
    assert stage_summary["stage_count"] == 1
    assert len(stage_summary["stages"]) == 1

    stage = stage_summary["stages"][0]
    dispatch_payloads = payload["domain_dispatch_payload_summaries"]
    success_payloads = [
        item for item in dispatch_payloads if item["mode"] == "refs_only_domain_owned_success_payload"
    ]
    blocker_payloads = [
        item
        for item in dispatch_payloads
        if item["mode"] == "refs_only_domain_owned_typed_blocker_payload"
    ]
    assert stage["stage_id"] == "finalize_and_publication_handoff"
    assert stage["sequence"] == 6
    assert stage["paper_line_count"] == len(dispatch_payloads)
    assert stage["success_payload_count"] == len(success_payloads)
    assert stage["typed_blocker_payload_count"] == len(blocker_payloads)
    assert stage["domain_owner_receipt_ref_count"] == sum(
        len(item["domain_owner_receipt_refs"]) for item in success_payloads
    )
    assert stage["stable_typed_blocker_ref_count"] == sum(
        len(item["typed_blocker_refs"]) for item in blocker_payloads
    )
    assert stage["stage_expected_receipt_ref_count"] == sum(
        len(item["stage_expected_receipt_refs"]) for item in dispatch_payloads
    )
    assert stage["stage_monitor_freshness_ref_count"] == sum(
        len(item["stage_monitor_freshness_refs"]) for item in dispatch_payloads
    )
    assert stage["no_forbidden_write_guard_ref_count"] == sum(
        len(item.get("forbidden_write_guard_refs", [])) for item in dispatch_payloads
    )
    assert stage["current_payload_template"] == {
        "domain_receipt_refs": [],
        "monitor_freshness_refs": [],
        "runtime_event_refs": [],
        "typed_blocker_refs": [],
    }
    assert stage["success_refs_path_source"] == (
        "domain_dispatch_payload_summaries[mode=refs_only_domain_owned_success_payload]"
    )
    assert stage["typed_blocker_path_source"] == (
        "domain_dispatch_payload_summaries[mode=refs_only_domain_owned_typed_blocker_payload]"
    )
    assert stage["success_refs_path_payload"] == {
        "domain_receipt_refs": [
            ref for item in success_payloads for ref in item["stage_expected_receipt_refs"]
        ],
        "monitor_freshness_refs": [
            ref for item in success_payloads for ref in item["stage_monitor_freshness_refs"]
        ],
        "runtime_event_refs": [],
        "typed_blocker_refs": [],
    }
    assert stage["typed_blocker_path_payload"] == {
        "domain_receipt_refs": [],
        "monitor_freshness_refs": [
            ref for item in blocker_payloads for ref in item["stage_monitor_freshness_refs"]
        ],
        "runtime_event_refs": [],
        "typed_blocker_refs": [
            ref for item in blocker_payloads for ref in item["typed_blocker_refs"]
        ],
    }
    assert stage["recommended_current_payload_path"] == "typed_blocker_path"
    assert stage["success_refs_visible_is_completion"] is False
    assert stage["typed_blocker_visible_is_domain_ready"] is False
    assert stage["domain_readiness_claimed"] is False
    assert stage["production_readiness_claimed"] is False
    assert stage["publication_readiness_claimed"] is False
    assert stage["artifact_mutation_authorized"] is False
    assert stage["current_package_mutation_authorized"] is False

    results = {item["paper_line_id"]: item for item in payload["paper_line_owner_chain_results"]}
    assert {item["paper_line_id"] for item in results.values() if item["result_kind"] == "owner_receipt"} == {
        "001-dm-cvd-mortality-risk",
        "002-dm-china-us-mortality-attribution",
        "003-dpcc-primary-care-phenotype-treatment-gap",
        "003-endocrine-burden-followup",
    }
    assert {item["paper_line_id"] for item in results.values() if item["result_kind"] == "stable_typed_blocker"} == {
        "004-dpcc-longitudinal-care-inertia-intensification-gap",
        "001-lineage-pfs",
        "002-early-residual-risk",
        "004-invasive-architecture",
        "obesity_multicenter_phenotype_atlas",
    }


def test_multiprofile_guarded_apply_snapshot_keeps_nfpitnet_numeric_ids_separate() -> None:
    payload = _snapshot()
    results = {item["paper_line_id"]: item for item in payload["paper_line_owner_chain_results"]}
    dispatches = {item["study_id"]: item for item in payload["domain_dispatch_payload_summaries"]}

    assert results["002-dm-china-us-mortality-attribution"]["result_kind"] == "owner_receipt"
    assert results["002-early-residual-risk"]["result_kind"] == "stable_typed_blocker"
    assert results["002-early-residual-risk"]["stable_typed_blocker_refs"] == [
        "mas_owner_apply_receipt_missing:002-early-residual-risk"
    ]
    assert results["003-dpcc-primary-care-phenotype-treatment-gap"]["owner_receipt_refs"] == [
        "/Users/gaofeng/workspace/Yang/DM-CVD-Mortality-Risk/studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/controller/gate_replay_requests/latest.json"
    ]
    assert results["003-endocrine-burden-followup"]["owner_receipt_refs"] == [
        "/Users/gaofeng/workspace/Yang/NF-PitNET/studies/003-endocrine-burden-followup/artifacts/controller/gate_replay_requests/latest.json"
    ]
    assert dispatches["002-early-residual-risk"]["mode"] == (
        "refs_only_domain_owned_typed_blocker_payload"
    )
    assert dispatches["003-endocrine-burden-followup"]["mode"] == (
        "refs_only_domain_owned_success_payload"
    )


def test_multiprofile_guarded_apply_snapshot_does_not_claim_domain_or_body_authority() -> None:
    payload = _snapshot()
    boundary = payload["authority_boundary"]

    assert boundary["domain_truth_owner"] == "med-autoscience"
    assert boundary["provider_attempt_owner"] == "one-person-lab"
    assert boundary["owner_chain_authority"] == "MedAutoScience"
    assert payload["opl_ingestable_surface"] == boundary["opl_ingestable_surface"]
    assert boundary["provider_completion_can_close_canary"] is False
    assert boundary["opl_records_refs_only"] is True
    assert boundary["opl_can_write_mas_truth"] is False
    assert boundary["opl_can_write_artifact_body"] is False
    assert boundary["opl_can_write_memory_body"] is False
    assert boundary["opl_can_write_current_package"] is False
    assert boundary["opl_can_authorize_quality_or_publication"] is False
    assert boundary["typed_blocker_is_domain_ready"] is False
    assert boundary["stage_expected_receipt_refs_close_domain_ready"] is False
    assert not any(payload["claim_boundary"].values())

    forbidden_keys = set(payload["forbidden_payload_fields"])
    for item in _walk_dicts(payload):
        assert not (forbidden_keys & set(item))
        if item.get("ref") and item.get("role"):
            assert item["body_included"] is False
        if "body_included" in item:
            assert item["body_included"] is False


def test_multiprofile_guarded_apply_snapshot_is_refs_only_and_replayable() -> None:
    payload = _snapshot()
    source = payload["source_live_proof"]

    assert "export_path" not in source
    assert "sha256" not in source
    assert source["compact_projection_sha256"] == _compact_projection_sha256(payload)
    assert source["body_included"] is False
    assert source["repo_tracks_live_proof_body"] is False
    assert source["command"].startswith(
        "scripts/run-python-clean.sh -m med_autoscience.cli real-paper-autonomy-guarded-apply-proof"
    )
    assert "nfpitnet.workspace.toml" in source["command"]
    assert "obesity.local.toml" in source["command"]

    memory_proof = payload["publication_route_memory_final_proof"]
    assert memory_proof["surface_kind"] == "dm002_publication_route_memory_final_proof"
    assert memory_proof["status"] == "final_ref_chain_proven"
    assert memory_proof["body_included"] is False
    assert memory_proof["memory_body_included"] is False
    assert memory_proof["opl_can_read_memory_body"] is False
    assert memory_proof["opl_can_accept_or_reject_writeback"] is False

    assert payload["verification_refs"] == [
        {
            "ref": "tests/test_mas_multiprofile_guarded_apply_receipt_scaleout_evidence.py",
            "role": "focused_contract_test",
            "body_included": False,
        },
        {
            "ref": "tests/test_real_paper_autonomy_soak_inventory_cases/test_study_identity_matching.py",
            "role": "identity_collision_regression_test",
            "body_included": False,
        },
        {
            "ref": "tests/test_real_paper_autonomy_soak_inventory_cases/test_canary_body_free_packets.py",
            "role": "canary_body_free_packet_shape_test",
            "body_included": False,
        },
    ]


def _compact_projection_sha256(payload: dict[str, object]) -> str:
    projection = {
        "evidence_id": payload["evidence_id"],
        "opl_ingestable_surface": payload["opl_ingestable_surface"],
        "live_summary": payload["live_summary"],
        "paper_line_owner_payload_summary": payload["paper_line_owner_payload_summary"],
        "stage_expected_receipt_payload_summary": payload[
            "stage_expected_receipt_payload_summary"
        ],
        "paper_line_identity_order": payload["paper_line_identity_order"],
        "paper_line_owner_chain_results": payload["paper_line_owner_chain_results"],
        "domain_dispatch_payload_summaries": payload["domain_dispatch_payload_summaries"],
        "publication_route_memory_final_proof": payload["publication_route_memory_final_proof"],
        "claim_boundary": payload["claim_boundary"],
    }
    rendered = json.dumps(projection, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()
