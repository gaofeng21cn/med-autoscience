from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.paper_mission.audit_pack import ref_kind
from med_autoscience.paper_mission.authority_boundary import PAPER_AUDIT_PACK_FAMILIES
from med_autoscience.paper_mission.payload_helpers import (
    dedupe,
    first_text,
    int_or_zero,
    mapping,
    mapping_list,
    text,
    text_items,
)
from med_autoscience.paper_mission_transaction import (
    build_paper_mission_transaction,
    stage_terminal_decision_for_consume_result,
)


def paper_mission_transaction_payload(
    *,
    mission: Mapping[str, Any],
    readback: Mapping[str, Any],
    consume_result: Mapping[str, Any],
) -> dict[str, Any]:
    current_mission = mapping(readback.get("current_mission"))
    required_output = mapping(readback.get("required_output"))
    mission_objective = mapping(readback.get("mission_objective"))
    stage_id = first_text((
        current_mission.get("objective_kind"),
        required_output.get("objective_kind"),
        mission_objective.get("objective_kind"),
        "paper_mission_stage",
    ))
    mission_id = text(mission.get("mission_id")) or "paper-mission::unknown"
    study_id = text(mission.get("study_id")) or "unknown_study"
    stage_run_ref = f"opl-stage-run://paper-mission-carrier/{study_id}/{stage_id}/{mission_id}"
    enriched_consume_result = _transaction_consume_result(
        consume_result=consume_result,
        readback=readback,
    )
    terminal_decision = stage_terminal_decision_for_consume_result(
        mission_id=mission_id,
        study_id=study_id,
        stage_id=stage_id,
        consume_result=enriched_consume_result,
        default_next_owner=first_text((
            required_output.get("next_owner"),
            readback.get("next_owner"),
            "mas_authority_kernel",
        )),
        default_next_stage_id=_next_stage_id_for_terminal_decision(
            stage_id=stage_id,
            required_output=required_output,
        ),
        default_next_work_unit=first_text((
            required_output.get("work_unit_id"),
            current_mission.get("objective_id"),
            stage_id,
        )),
        default_reason=_terminal_decision_reason(
            consume_result=enriched_consume_result,
            readback=readback,
        ),
    )
    return build_paper_mission_transaction(
        mission_id=mission_id,
        study_id=study_id,
        stage_id=stage_id,
        stage_run_ref=stage_run_ref,
        terminal_decision=terminal_decision,
        artifact_delta_refs=_transaction_artifact_delta_refs(mission),
        paper_audit_pack_refs=_transaction_audit_pack_refs(mission),
        idempotency_basis=first_text((
            enriched_consume_result.get("outcome"),
            enriched_consume_result.get("status"),
            stage_id,
        )),
    )


def refs_with_kinds(refs: list[str], kinds: set[str]) -> list[str]:
    return [ref for ref in refs if ref_kind(ref) in kinds]


def platform_count(domain_diagnostic: Mapping[str, Any], key: str) -> int:
    provider_state = mapping(domain_diagnostic.get("provider_admission_current_control_state"))
    return int_or_zero(provider_state.get(key))


def progress_payloads_by_study(
    payloads: Mapping[str, Any] | Iterable[Mapping[str, Any]],
) -> dict[str, Mapping[str, Any]]:
    if isinstance(payloads, Mapping) and isinstance(payloads.get("study_id"), str):
        study_id = str(payloads["study_id"])
        return {study_id: payloads}
    if isinstance(payloads, Mapping):
        by_study: dict[str, Mapping[str, Any]] = {}
        for key, value in payloads.items():
            mapped = mapping(value)
            study_id = text(mapped.get("study_id")) or str(key)
            by_study[study_id] = mapped
        return by_study
    by_study = {}
    for payload in payloads:
        mapped = mapping(payload)
        study_id = text(mapped.get("study_id"))
        if not study_id:
            raise ValueError("study progress payload missing study_id")
        by_study[study_id] = mapped
    return by_study


def work_unit_ids(items: object) -> list[str]:
    ids: list[str] = []
    for item in mapping_list(items):
        ids.extend(text_items((item.get("unit_id"), item.get("work_unit_id"))))
    return dedupe(ids)


def _transaction_consume_result(
    *,
    consume_result: Mapping[str, Any],
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    enriched = dict(consume_result)
    consume_readback = mapping(readback.get("consume_candidate_readback"))
    if not enriched.get("resume_condition"):
        enriched["resume_condition"] = first_text((
            consume_readback.get("resume_condition"),
            mapping(consume_readback.get("route_back")).get("resume_condition"),
            mapping(consume_readback.get("typed_blocker_required")).get("resume_condition"),
            mapping(consume_readback.get("human_gate_required")).get("resume_condition"),
        ))
    typed_blocker = mapping(consume_readback.get("typed_blocker_required"))
    if typed_blocker:
        enriched["blocker_id"] = first_text((
            typed_blocker.get("blocker_id"),
            enriched.get("blocker_id"),
        ))
        enriched["unblock_condition"] = first_text((
            typed_blocker.get("resume_condition"),
            enriched.get("unblock_condition"),
            enriched.get("resume_condition"),
        ))
    human_gate = mapping(consume_readback.get("human_gate_required"))
    if human_gate:
        enriched["question"] = first_text((
            human_gate.get("question"),
            enriched.get("question"),
        ))
        enriched["required_receipt"] = first_text((
            human_gate.get("decision_packet_ref"),
            enriched.get("required_receipt"),
        ))
    return enriched


def _terminal_decision_reason(
    *,
    consume_result: Mapping[str, Any],
    readback: Mapping[str, Any],
) -> str:
    return first_text((
        consume_result.get("reason"),
        consume_result.get("outcome"),
        readback.get("consume_candidate_status"),
        "mas_stage_terminalized_from_paper_mission_candidate",
    ))


def _next_stage_id_for_terminal_decision(
    *,
    stage_id: str,
    required_output: Mapping[str, Any],
) -> str:
    objective_kind = text(required_output.get("objective_kind")) or stage_id
    if objective_kind == "gate_clearing_claim_evidence_repair":
        return "publication_gate_replay"
    if objective_kind == "medical_prose_write_repair_publication_gate_replay":
        return "publication_quality_recheck"
    return f"{stage_id}::next"


def _transaction_artifact_delta_refs(mission: Mapping[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for index, delta in enumerate(mapping_list(mission.get("artifact_delta_ledger")), start=1):
        uri = text(delta.get("artifact_ref"))
        if not uri:
            continue
        refs.append(
            {
                "ref_id": text(delta.get("delta_id")) or f"artifact_delta::{index}",
                "ref_kind": text(delta.get("delta_kind")) or "artifact_delta",
                "uri": uri,
            }
        )
    if refs:
        return refs
    return [
        {
            "ref_id": "artifact_delta::missing",
            "ref_kind": "missing_artifact_delta",
            "uri": "mission://artifact-delta/missing",
        }
    ]


def _transaction_audit_pack_refs(mission: Mapping[str, Any]) -> dict[str, list[dict[str, str]]]:
    audit_pack = mapping(mission.get("paper_audit_pack"))
    refs_by_family: dict[str, list[dict[str, str]]] = {}
    for family in PAPER_AUDIT_PACK_FAMILIES:
        family_payload = mapping(audit_pack.get(family))
        refs = [
            {
                "ref_id": text(ref.get("ref_id")) or f"{family}::{index}",
                "ref_kind": text(ref.get("ref_kind")) or "artifact_ref",
                "uri": text(ref.get("uri")) or f"mission://audit-pack/{family}/missing",
            }
            for index, ref in enumerate(mapping_list(family_payload.get("refs")), start=1)
        ]
        if not refs:
            refs = [
                {
                    "ref_id": f"{family}::missing",
                    "ref_kind": "missing_audit_ref",
                    "uri": f"mission://audit-pack/{family}/missing",
                }
            ]
        refs_by_family[family] = refs
    return refs_by_family
