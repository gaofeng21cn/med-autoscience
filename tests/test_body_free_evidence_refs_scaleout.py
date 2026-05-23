from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any, Mapping

import pytest


PACKET_KEYS = {
    "ref",
    "role",
    "freshness",
    "owner",
    "receipt_id",
    "no_forbidden_write_proof",
}
FORBIDDEN_BODY_KEYS = {
    "memory_body",
    "artifact_body",
    "publication_verdict",
    "publication_verdict_body",
    "current_package_body",
}


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _assert_body_free_packet(packet: Mapping[str, Any], *, role: str, owner: str) -> None:
    assert set(packet) == PACKET_KEYS
    assert packet["role"] == role
    assert packet["owner"] == owner
    assert packet["ref"]
    assert packet["receipt_id"]
    proof = packet["no_forbidden_write_proof"]
    assert proof["write_permitted"] is False
    assert proof["forbidden_writes_performed"] is False
    assert proof["memory_body_write_performed"] is False
    assert proof["artifact_body_write_performed"] is False
    assert proof["publication_verdict_write_performed"] is False
    assert proof["current_package_write_performed"] is False
    assert not (set(packet) & FORBIDDEN_BODY_KEYS)


def test_publication_route_memory_receipt_inventory_projects_accepted_rejected_and_blocked_body_free_refs(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.stage_knowledge_plane_parts.publication_route_memory_inventory"
    )
    receipt_root = (
        tmp_path
        / "workspace"
        / "portfolio"
        / "research_memory"
        / "publication_route_memory"
        / "writeback_receipts"
    )
    _write_json(
        receipt_root / "accepted.json",
        {
            "status": "applied",
            "stage": "decision",
            "memory_family": "publication_route_memory",
            "accepted_writes": [
                {
                    "write_id": "accepted-route",
                    "destination": "workspace_research_memory_proposal",
                    "owner_target": "workspace_memory_owner",
                    "payload": {
                        "lesson": "MEMORY_BODY_SHOULD_NOT_APPEAR",
                        "route_family": "route_back_repair",
                    },
                }
            ],
        },
    )
    _write_json(
        receipt_root / "rejected.json",
        {
            "status": "applied",
            "stage": "review",
            "memory_family": "publication_route_memory",
            "rejected_writes": [
                {
                    "write_id": "rejected-route",
                    "destination": "workspace_research_memory_proposal",
                    "reason": "study_specific_claim_not_workspace_memory",
                    "payload": {"lesson": "REJECTED_MEMORY_BODY_SHOULD_NOT_APPEAR"},
                }
            ],
        },
    )
    _write_json(
        receipt_root / "blocked.json",
        {
            "status": "blocked",
            "stage": "idea",
            "memory_family": "publication_route_memory",
            "typed_blockers": [
                {
                    "blocker_id": "memory_writeback_owner_missing",
                    "reason": "workspace_memory_owner_receipt_missing",
                }
            ],
        },
    )

    inventory = module.build_publication_route_memory_inventory(workspace_root=tmp_path / "workspace")
    receipts = inventory["opl_aion_receipt_inventory"]["receipts"]
    packets = [packet for receipt in receipts for packet in receipt["body_free_evidence_packets"]]

    assert {packet["role"] for packet in packets} == {
        "accepted_memory_receipt_ref",
        "rejected_memory_receipt_ref",
        "blocked_memory_receipt_ref",
    }
    for packet in packets:
        _assert_body_free_packet(packet, role=packet["role"], owner="MedAutoScience")
    assert inventory["opl_aion_receipt_inventory"]["receipt_review_summary"]["blocked_writeback_ref_count"] == 1
    rendered = json.dumps(inventory, ensure_ascii=False)
    assert "MEMORY_BODY_SHOULD_NOT_APPEAR" not in rendered
    assert "REJECTED_MEMORY_BODY_SHOULD_NOT_APPEAR" not in rendered


def test_artifact_lifecycle_retention_plan_projects_mutation_restore_and_retention_body_free_refs(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_retention_operations_plan")
    artifacts = [
        {
            "path": str(tmp_path / "studies" / "001" / "paper" / "source" / "manuscript.md"),
            "workspace_relative_path": "studies/001/paper/source/manuscript.md",
            "role": "canonical_source",
            "lifecycle": "active_authority",
            "cleanup_candidate_action": "keep-online",
            "cleanup_blockers": [],
        },
        {
            "path": str(tmp_path / "studies" / "001" / "manuscript" / "current_package" / "paper.pdf"),
            "workspace_relative_path": "studies/001/manuscript/current_package/paper.pdf",
            "role": "derived_projection",
            "lifecycle": "rebuildable_projection",
            "cleanup_candidate_action": "rebuildable",
            "cleanup_blockers": [],
        },
        {
            "path": str(tmp_path / "ops" / "runtime" / "quests" / "001" / ".ds" / "cold_archive" / "payload.tar.gz"),
            "workspace_relative_path": "ops/runtime/quests/001/.ds/cold_archive/payload.tar.gz",
            "role": "cold_archive",
            "lifecycle": "archived_restore_candidate",
            "cleanup_candidate_action": "restore-gated",
            "cleanup_blockers": [],
        },
    ]

    plan = module.build_artifact_retention_operations_plan(workspace_root=tmp_path, artifacts=artifacts)
    packets = [operation["body_free_evidence_packet"] for operation in plan["operations"]]

    assert {packet["role"] for packet in packets} == {
        "artifact_retention_receipt_ref",
        "artifact_mutation_receipt_ref",
        "artifact_restore_receipt_ref",
    }
    for packet in packets:
        _assert_body_free_packet(packet, role=packet["role"], owner="MedAutoScience")
    assert all(packet["no_forbidden_write_proof"]["artifact_body_write_performed"] is False for packet in packets)


def test_human_gate_resume_receipt_consumption_includes_body_free_resume_ref(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_transition_receipt_consumption")
    study_root = tmp_path / "workspace" / "studies" / "002-human-gate"
    decision_id = "study-decision::002-human-gate::quest-002::resume::2026-05-15T09:00:00+00:00"
    controller_decision = {
        "decision_id": decision_id,
        "requires_human_confirmation": True,
        "family_human_gates": [{"gate_id": "controller-human-confirmation-002-human-gate"}],
    }
    _write_json(
        study_root / "artifacts" / "controller" / "controller_confirmation_summary.json",
        {
            "decision_ref": {"decision_id": decision_id},
            "gate_id": "controller-human-confirmation-002-human-gate",
            "status": "approved",
            "controller_action_types": ["ensure_study_runtime"],
        },
    )

    receipt = module.human_gate_resume_receipt_consumption(
        study_root=study_root,
        controller_decision=controller_decision,
        controller_decision_ref=Path("artifacts/controller_decisions/latest.json"),
    )

    assert receipt["receipt_kind"] == "human_gate_resume_receipt"
    _assert_body_free_packet(
        receipt["body_free_evidence_packet"],
        role="human_gate_or_resume_ref",
        owner="MedAutoScience",
    )


def test_provider_slo_long_soak_read_model_projects_body_free_provider_refs() -> None:
    adapter = importlib.import_module("med_autoscience.controllers.opl_provider_ready_adapter")

    read_model = adapter.build_provider_residency_read_model(
        provider_available=True,
        receipt_refs={
            "temporal_production_residency": "opl://provider/temporal-residency.json",
            "worker_restart_requery": "opl://provider/worker-restart.json",
            "retry_dead_letter": "opl://provider/retry-dead-letter.json",
            "long_soak_receipt": "opl://provider/long-soak.json",
        },
    )

    packets = read_model["body_free_evidence_packets"]
    assert {packet["role"] for packet in packets} == {
        "provider_residency_ref",
        "restart_requery_ref",
        "retry_dead_letter_ref",
        "provider_slo_long_soak_ref",
    }
    for packet in packets:
        _assert_body_free_packet(packet, role=packet["role"], owner="one-person-lab")
    assert read_model["authority_boundary"]["can_write_domain_truth"] is False
    assert read_model["authority_boundary"]["can_write_current_package"] is False
    assert read_model["authority_boundary"]["can_authorize_publication_quality"] is False


def test_body_free_evidence_packet_rejects_forbidden_body_fields() -> None:
    module = importlib.import_module("med_autoscience.controllers.body_free_evidence_packets")

    packet = module.build_body_free_evidence_packet(
        ref="artifacts/controller_decisions/latest.json",
        role="human_gate_or_resume_ref",
        owner="MedAutoScience",
    )
    _assert_body_free_packet(packet, role="human_gate_or_resume_ref", owner="MedAutoScience")

    with pytest.raises(ValueError, match="forbidden body fields"):
        module.assert_body_free_evidence_packet(
            {
                **packet,
                "no_forbidden_write_proof": {
                    **packet["no_forbidden_write_proof"],
                    "memory_body": "must fail",
                },
            }
        )


def test_domain_dispatch_evidence_record_payload_is_opl_preflight_ready_refs_only() -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_dispatch_evidence_payload")

    payload = module.build_domain_dispatch_evidence_record_payload(
        task_kind="domain_route/owner-handoff",
        study_id="DM002",
        reason="quest_waiting_opl_runtime_owner_route",
        evidence_refs=[
            "studies/DM002/artifacts/supervision/owner_route_handoff/latest.json",
            {"ref": "studies/DM002/artifacts/controller_decisions/latest.json"},
        ],
        source_fingerprint="abc123",
    )

    assert payload["surface_kind"] == "mas_domain_dispatch_evidence_record_payload"
    assert payload["version"] == "mas-domain-dispatch-evidence-record-payload.v1"
    assert payload["body_included"] is False
    assert payload["domain_ready_claimed"] is False
    assert payload["source_fingerprint"] == "abc123"
    assert payload["record_payload"]["typed_blocker_refs"]
    assert {
        key: payload["record_payload"][key]
        for key in ("domain_id", "task_kind", "study_id", "source_fingerprint", "domain_source_fingerprint")
    } == {
        "domain_id": "medautoscience",
        "task_kind": "domain_route/owner-handoff",
        "study_id": "DM002",
        "source_fingerprint": "abc123",
        "domain_source_fingerprint": "abc123",
    }
    assert payload["record_payload"]["evidence_refs"] == [
        "studies/DM002/artifacts/supervision/owner_route_handoff/latest.json",
        "studies/DM002/artifacts/controller_decisions/latest.json",
        "contracts/production_acceptance/mas-production-acceptance.json"
        "#/paper_line_guarded_apply_evidence",
    ]
    assert payload["record_payload"]["no_regression_refs"]
    assert "receipt_ref" not in payload["record_payload"]
    assert payload["ledger_receipt_ref_hint"].startswith(
        "mas://domain-dispatch-evidence/medautoscience/"
    )
    assert {
        packet["role"] for packet in payload["body_free_evidence_packets"]
    } == {"stable_typed_blocker_ref", "no_forbidden_write_proof_ref"}
    for packet in payload["body_free_evidence_packets"]:
        _assert_body_free_packet(packet, role=packet["role"], owner="MedAutoScience")
    assert payload["authority_boundary"]["opl_records_refs_only"] is True
    assert payload["authority_boundary"]["provider_completion_is_domain_ready"] is False
    rendered = json.dumps(payload, ensure_ascii=False)
    assert "current_package_body" in payload["forbidden_payload_fields"]
    assert "study_truth_body" in payload["forbidden_payload_fields"]
    assert "MEMORY_BODY_SHOULD_NOT_APPEAR" not in rendered
