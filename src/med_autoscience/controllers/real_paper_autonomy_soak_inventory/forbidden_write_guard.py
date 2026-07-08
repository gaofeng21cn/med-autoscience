from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.controllers import opl_provider_ready_adapter


def build_provider_forbidden_write_guard(*, closeout_packets: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    packet_guards = [
        opl_provider_ready_adapter.build_forbidden_write_guard_proof(
            result="accepted_no_forbidden_writes",
            task_id=_text(packet.get("closeout_id")),
            task_kind="domain_stage_closeout_packet",
            requested_writes=(),
        )
        for packet in closeout_packets
    ]
    blocked_probe = opl_provider_ready_adapter.build_forbidden_write_guard_proof(
        result="blocked",
        task_id="provider-hosted-paper-proof:forbidden-write-probe",
        task_kind="provider_hosted_paper_proof",
        requested_writes=opl_provider_ready_adapter.FORBIDDEN_AUTHORITY_WRITES,
    )
    return {
        "surface_kind": "mas_provider_hosted_forbidden_write_guard_summary",
        "aggregate_result": "fail_closed_no_forbidden_writes",
        "guard_mode": "fail_closed",
        "packet_guard_count": len(packet_guards),
        "packet_guards": packet_guards,
        "blocked_probe": blocked_probe,
        "can_write_domain_truth": False,
        "can_write_current_package": False,
        "can_authorize_publication_quality": False,
        "can_write_memory_body": False,
        "can_accept_memory_writeback": False,
    }


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["build_provider_forbidden_write_guard"]
