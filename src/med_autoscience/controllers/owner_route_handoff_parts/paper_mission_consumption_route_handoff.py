from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Mapping

from .export_study_projection import mapping, text


def latest_paper_mission_consumption_route_handoff(
    *,
    workspace_root: Path,
    study_id: str,
    paper_mission_transaction_ref: str | None = None,
    route_identity_key: str | None = None,
) -> dict[str, Any] | None:
    ledger_root = (
        workspace_root
        / "ops"
        / "medautoscience"
        / "paper_mission_consumption_ledger"
    )
    if not ledger_root.exists():
        return None
    candidates: list[tuple[int, float, str, str, dict[str, Any]]] = []
    for handoff_ref in ledger_root.glob(f"**/{study_id}/opl_route_handoff.json"):
        try:
            payload = json.loads(handoff_ref.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        handoff = _valid_paper_mission_consumption_route_handoff(
            payload,
            study_id=study_id,
            source_ref=handoff_ref,
        )
        if handoff is None:
            continue
        if not _matches_requested_identity(
            handoff,
            paper_mission_transaction_ref=paper_mission_transaction_ref,
            route_identity_key=route_identity_key,
        ):
            continue
        try:
            mtime = handoff_ref.stat().st_mtime
        except OSError:
            mtime = 0.0
        candidates.append(
            (
                _candidate_external_delta_priority(
                    text(handoff.get("candidate_ref")),
                ),
                mtime,
                _paper_mission_handoff_timestamp_key(handoff_ref),
                str(handoff_ref),
                handoff,
            )
        )
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item[0], item[1], item[2], item[3]))[4]


def paper_mission_handoff_stage_packet_refs(
    handoff: Mapping[str, Any],
    *,
    fallback_refs: list[str],
) -> list[str]:
    carrier = mapping(handoff.get("opl_runtime_carrier"))
    refs = [
        text(carrier.get("stage_run_ref")),
        text(handoff.get("paper_mission_transaction_ref")),
        text(handoff.get("opl_route_command_ref")),
        text(handoff.get("candidate_ref")),
        text(handoff.get("source_ref")),
        *fallback_refs,
    ]
    return list(dict.fromkeys(ref for ref in refs if ref))


def _matches_requested_identity(
    handoff: Mapping[str, Any],
    *,
    paper_mission_transaction_ref: str | None,
    route_identity_key: str | None,
) -> bool:
    transaction_ref = text(paper_mission_transaction_ref)
    route_key = text(route_identity_key)
    carrier = mapping(handoff.get("opl_runtime_carrier"))
    if transaction_ref is not None and text(handoff.get("paper_mission_transaction_ref")) != transaction_ref:
        return False
    if route_key is not None and text(carrier.get("route_identity_key")) != route_key:
        return False
    return True


def _paper_mission_handoff_timestamp_key(handoff_ref: Path) -> str:
    for part in reversed(handoff_ref.parts):
        match = re.search(r"20\d{6}[TZ][0-9A-Za-z_-]+", part)
        if match:
            return match.group(0)
    return ""


def _candidate_external_delta_priority(candidate_ref: str | None) -> int:
    if not candidate_ref:
        return 0
    try:
        payload = json.loads(Path(candidate_ref).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    manifest = mapping(payload)
    delta = mapping(manifest.get("paper_facing_candidate_delta"))
    return int(
        bool(
            text(manifest.get("adopted_external_paper_delta_ref"))
            or text(delta.get("adopted_external_paper_delta_ref"))
        )
    )


def _valid_paper_mission_consumption_route_handoff(
    payload: Mapping[str, Any],
    *,
    study_id: str,
    source_ref: Path,
) -> dict[str, Any] | None:
    if payload.get("surface_kind") != "mas_paper_mission_opl_route_handoff_record":
        return None
    if text(payload.get("study_id")) != study_id:
        return None
    if payload.get("handoff_status") != "ready_for_opl_route_command":
        return None
    if payload.get("can_submit_to_opl_runtime") is not True:
        return None
    if payload.get("transaction_materialized") is not True:
        return None
    command_kind = text(payload.get("route_command_kind")) or text(
        mapping(payload.get("opl_route_command")).get("command_kind")
    )
    if command_kind not in {"start_next_stage", "resume_stage", "route_back"}:
        return None
    if not _same_handoff_carrier_identity(payload):
        return None
    if any(
        payload.get(flag) is True
        for flag in (
            "can_claim_opl_runtime_enqueued",
            "can_claim_opl_stage_run_created",
            "can_claim_provider_running",
            "can_claim_paper_progress",
            "can_claim_runtime_ready",
        )
    ):
        return None
    authority = mapping(payload.get("authority_boundary"))
    if not authority:
        return None
    forbidden_flags = (
        "writes_authority_surface",
        "writes_publication_eval",
        "writes_controller_decision",
        "can_write_owner_receipt",
        "can_write_typed_blocker",
        "can_write_human_gate",
        "can_write_current_package",
        "can_write_paper_body",
        "can_write_runtime_queue",
        "can_write_opl_outbox",
        "can_write_opl_event",
        "can_write_opl_stage_run",
        "can_write_provider_attempt",
        "writes_owner_receipt",
        "writes_typed_blocker",
        "writes_human_gate",
        "writes_current_package",
        "writes_paper_body",
        "writes_runtime_queue",
        "writes_opl_outbox",
        "writes_opl_event",
        "writes_opl_stage_run",
        "writes_provider_attempt",
        "writes_yang_authority",
    )
    if any(
        payload.get(flag) is True or authority.get(flag) is True
        for flag in forbidden_flags
    ):
        return None
    return {
        **dict(payload),
        "source_ref": str(source_ref),
        "source_surface_kind": "mas_paper_mission_opl_route_handoff_record",
        "paper_mission_default_handoff_source": "paper_mission_consumption_ledger",
    }


def _same_handoff_carrier_identity(payload: Mapping[str, Any]) -> bool:
    transaction_ref = text(payload.get("paper_mission_transaction_ref"))
    stage_ref = text(payload.get("stage_terminal_decision_ref"))
    route_ref = text(payload.get("opl_route_command_ref"))
    route = mapping(payload.get("opl_route_command"))
    carrier = mapping(payload.get("opl_runtime_carrier"))
    if not transaction_ref or not stage_ref or not route_ref:
        return False
    if stage_ref != f"{transaction_ref}#stage_terminal_decision":
        return False
    if route_ref != f"{transaction_ref}#opl_route_command":
        return False
    if text(route.get("source_terminal_decision_ref")) != stage_ref:
        return False
    if not carrier:
        return False
    if text(carrier.get("surface_kind")) != "mas_domain_progress_transition_request":
        return False
    if text(carrier.get("source_kind")) != "paper_mission_transaction_opl_route_command":
        return False
    if carrier.get("projection_only") is not True:
        return False
    if text(carrier.get("paper_mission_transaction_ref")) != transaction_ref:
        return False
    if text(carrier.get("stage_terminal_decision_ref")) != stage_ref:
        return False
    if text(carrier.get("opl_route_command_ref")) != route_ref:
        return False
    if text(carrier.get("study_id")) != text(payload.get("study_id")):
        return False
    idempotency_key = text(carrier.get("idempotency_key"))
    if text(carrier.get("route_identity_key")) != f"{transaction_ref}::route":
        return False
    if not idempotency_key:
        return False
    if text(carrier.get("attempt_idempotency_key")) != (
        f"{idempotency_key}::opl-attempt"
    ):
        return False
    if text(carrier.get("request_idempotency_key")) != (
        f"{idempotency_key}::opl-request"
    ):
        return False
    if mapping(carrier.get("opl_route_command")) != route:
        return False
    aggregate = mapping(carrier.get("aggregate_identity"))
    if text(aggregate.get("aggregate_id")) != transaction_ref:
        return False
    if text(aggregate.get("study_id")) != text(payload.get("study_id")):
        return False
    if text(aggregate.get("work_unit_id")) != text(carrier.get("work_unit_id")):
        return False
    if text(aggregate.get("work_unit_fingerprint")) != text(
        carrier.get("work_unit_fingerprint")
    ):
        return False
    return True


__all__ = [
    "latest_paper_mission_consumption_route_handoff",
    "paper_mission_handoff_stage_packet_refs",
]
