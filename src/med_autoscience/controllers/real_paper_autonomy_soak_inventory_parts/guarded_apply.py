from __future__ import annotations
from collections.abc import Iterable, Mapping, Sequence
from typing import Any


SOAK_EVIDENCE_STATES = {
    "artifact_delta",
    "gate_replay",
    "ai_reviewer_re_eval",
    "route_decision",
    "stop_loss",
    "human_gate",
    "stable_blocker",
    "continuing_repair",
}


def build_guarded_apply_proof_from_provider_proof(
    *,
    provider_proof: Mapping[str, Any],
    schema_version: int,
    surface: str,
    target_studies: Sequence[str],
) -> dict[str, Any]:
    closeout_packets = [dict(_mapping(packet)) for packet in provider_proof.get("typed_closeout_packets", [])]
    guarded_receipts = [_guarded_apply_receipt(packet) for packet in closeout_packets]
    accepted_receipts = [receipt for receipt in guarded_receipts if receipt.get("apply_result") != "typed_blocker"]
    typed_blockers = [receipt for receipt in guarded_receipts if receipt.get("apply_result") == "typed_blocker"]
    mutation_receipts = [
        receipt
        for receipt in accepted_receipts
        if _receipt_observes_workspace_mutation(receipt)
    ]
    owner_receipt_observed = bool(accepted_receipts)
    guarded_apply_performed = bool(mutation_receipts)
    memory_final_proof = _dm002_publication_route_memory_final_proof(closeout_packets)
    forbidden_guard = _mapping(provider_proof.get("forbidden_write_guard"))
    return {
        "surface": surface,
        "schema_version": schema_version,
        "mode": "mas_owned_guarded_apply_proof",
        "guarded_apply_status": (
            "mas_owner_apply_receipt_observed"
            if owner_receipt_observed
            else "blocked_no_mas_owner_apply_receipt"
        ),
        "provider_attempt_projection": {
            **dict(_mapping(provider_proof.get("provider_attempt_projection"))),
            "guarded_apply_performed": guarded_apply_performed,
            "provider_attempt_wrote_workspace": False,
            "mas_owner_receipt_required": True,
            "can_advance_paper_progress_without_mas_owner_receipt": False,
        },
        "guarded_apply_receipts": guarded_receipts,
        "publication_route_memory_final_proof": memory_final_proof,
        "forbidden_write_guard": dict(forbidden_guard),
        "summary": {
            "target_study_count": len(target_studies),
            "guarded_receipt_count": len(guarded_receipts),
            "typed_blocker_count": len(typed_blockers),
            "mas_owner_apply_receipt_count": len(accepted_receipts),
            "artifact_delta_or_gate_progress_count": len(mutation_receipts),
            "memory_final_proof_status": memory_final_proof["status"],
            "forbidden_write_guard_result": forbidden_guard.get("aggregate_result"),
            "writes_performed": guarded_apply_performed,
            "real_workspace_mutation_allowed": guarded_apply_performed,
            "guarded_apply_performed": guarded_apply_performed,
            "mas_owner_receipt_observed": owner_receipt_observed,
        },
        "authority_boundary": _guarded_apply_authority_boundary(),
        "source_provider_proof_summary": {
            "surface": provider_proof.get("surface"),
            "schema_version": provider_proof.get("schema_version"),
            "mode": provider_proof.get("mode"),
            "provider_hosted_status": provider_proof.get("provider_hosted_status"),
            "summary": dict(_mapping(provider_proof.get("summary"))),
        },
    }


def _guarded_apply_receipt(packet: Mapping[str, Any]) -> dict[str, Any]:
    study_id = _text(_mapping(packet.get("route_impact")).get("study_id")) or _text(packet.get("closeout_id"))
    verdict = _text(packet.get("domain_ready_verdict")) or "typed_blocker"
    owner_refs = _mas_owner_apply_receipt_refs(packet)
    progress_observed = bool(owner_refs) and verdict in SOAK_EVIDENCE_STATES
    if not progress_observed:
        return {
            "surface_kind": "mas_guarded_apply_receipt",
            "version": "mas-guarded-apply-proof.v1",
            "study_id": study_id,
            "closeout_id": _text(packet.get("closeout_id")),
            "apply_result": "typed_blocker",
            "domain_ready_verdict": verdict,
            "mas_owner_apply_receipt_refs": owner_refs,
            "typed_blocker": {
                "blocker_id": f"mas_owner_apply_receipt_missing:{_normalize_study_id(study_id)}",
                "study_id": study_id,
                "owner": "MedAutoScience",
                "reason": (
                    "no MAS owner apply receipt with artifact delta, gate replay, route decision, human gate, "
                    "stop-loss, or stable blocker was observed"
                ),
                "required_owner_surface": "MAS owner gate / guarded apply contract",
                "write_permitted": False,
            },
            "workspace_mutation": _workspace_mutation_summary(allowed=False),
            "source_refs": list(packet.get("consumed_refs") or []),
            "authority_boundary": _guarded_apply_authority_boundary(),
        }
    return {
        "surface_kind": "mas_guarded_apply_receipt",
        "version": "mas-guarded-apply-proof.v1",
        "study_id": study_id,
        "closeout_id": _text(packet.get("closeout_id")),
        "apply_result": verdict,
        "domain_ready_verdict": verdict,
        "mas_owner_apply_receipt_refs": owner_refs,
        "typed_blocker": None,
        "workspace_mutation": _workspace_mutation_summary(
            allowed=_verdict_observes_workspace_mutation(verdict),
        ),
        "source_refs": list(packet.get("consumed_refs") or []),
        "authority_boundary": _guarded_apply_authority_boundary(),
    }


def _mas_owner_apply_receipt_refs(packet: Mapping[str, Any]) -> list[str]:
    evidence = _mapping(packet.get("mas_owner_apply_evidence"))
    if evidence.get("has_mas_owner_apply_receipt") is not True:
        return []
    return _dedupe_text(evidence.get("receipt_refs", []))


def _workspace_mutation_summary(*, allowed: bool) -> dict[str, Any]:
    return {
        "allowed_by_mas_owner_gate": allowed,
        "writes_performed": allowed,
        "mutation_owner": "med-autoscience" if allowed else "",
        "provider_attempt_wrote_workspace": False,
        "forbidden_surfaces": [
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
            "current_package",
            "publication_quality_verdict",
            "memory_body",
        ],
    }


def _receipt_observes_workspace_mutation(receipt: Mapping[str, Any]) -> bool:
    return _mapping(receipt.get("workspace_mutation")).get("writes_performed") is True


def _verdict_observes_workspace_mutation(verdict: str) -> bool:
    return verdict in {"artifact_delta", "gate_replay", "route_decision", "stop_loss", "human_gate"}


def _dm002_publication_route_memory_final_proof(closeout_packets: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    dm002_packet = next(
        (
            packet
            for packet in closeout_packets
            if _normalize_study_id(_text(_mapping(packet.get("route_impact")).get("study_id"))) == "002"
            or _normalize_study_id(_text(packet.get("closeout_id"))) == "002"
        ),
        {},
    )
    consumed_refs = _dedupe_text(dm002_packet.get("consumed_memory_refs", []))
    writeback_refs = _dedupe_text(dm002_packet.get("writeback_receipt_refs", []))
    ready = bool(consumed_refs and writeback_refs)
    return {
        "surface_kind": "dm002_publication_route_memory_final_proof",
        "target_study": "DM002",
        "status": "final_ref_chain_proven" if ready else "typed_blocker_missing_ref_chain",
        "consumed_refs": consumed_refs,
        "writeback_receipt_refs": writeback_refs,
        "body_included": False,
        "memory_body_included": False,
        "opl_can_read_memory_body": False,
        "opl_can_accept_or_reject_writeback": False,
        "mas_memory_owner": "med-autoscience",
        "typed_blocker": None
        if ready
        else {
            "blocker_id": "dm002_publication_route_memory_final_ref_chain_missing",
            "owner": "MedAutoScience",
            "reason": "DM002 closeout did not expose both consumed publication-route memory refs and MAS writeback receipt refs",
            "write_permitted": False,
        },
    }


def _guarded_apply_authority_boundary() -> dict[str, Any]:
    return {
        "projection_owner": "med-autoscience",
        "provider_attempt_owner": "one-person-lab",
        "domain_truth_owner": "med-autoscience",
        "quality_gate_owner": "med-autoscience",
        "artifact_authority_owner": "med-autoscience",
        "workspace_mutation_owner": "med-autoscience",
        "provider_attempt_is_truth": False,
        "provider_completion_is_publication_quality": False,
        "opl_can_write_mas_truth": False,
        "opl_can_write_artifact_authority": False,
        "opl_can_write_memory_body": False,
        "mutation_requires_mas_owner_gate": True,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _dedupe_text(values: Iterable[object]) -> list[str]:
    return list(dict.fromkeys(_text(value) for value in values if _text(value)))


def _normalize_study_id(study_id: str) -> str:
    text = str(study_id or "").strip().lower().replace("_", "-")
    aliases = {
        "dm002": "002",
        "dm-002": "002",
        "dm003": "003",
        "dm-003": "003",
        "obesity": "obesity",
    }
    if text in aliases:
        return aliases[text]
    if text.startswith("002-"):
        return "002"
    if text.startswith("003-"):
        return "003"
    if "obesity" in text:
        return "obesity"
    return text


__all__ = ["build_guarded_apply_proof_from_provider_proof"]
