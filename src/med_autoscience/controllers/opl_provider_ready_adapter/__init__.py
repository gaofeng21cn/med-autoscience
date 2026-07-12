from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any


TARGET_DOMAIN_ID = "mas"
DOMAIN_OWNER = "med-autoscience"

FORBIDDEN_AUTHORITY_WRITES = (
    "study_truth_write",
    "publication_quality_verdict",
    "artifact_gate_override",
    "current_package_write",
    "evidence_ledger_write",
    "review_ledger_write",
    "study_truth",
    "publication_eval",
    "publication_eval_write",
    "controller_decisions",
    "controller_decisions_write",
    "current_package",
    "paper/current_package",
    "manuscript/current_package",
    "paper/manuscript/current_package",
    "current_package.zip",
    "artifact_gate",
    "artifact_authority",
    "publication_authority",
    "publication_authority_write",
    "evidence_ledger",
    "memory_body_write",
    "review_ledger",
    "publication_route_memory_body",
    "publication_route_memory_writeback_accept",
    "memory_write_router_accept",
)


def requested_writes_from_task(task: Mapping[str, Any]) -> list[str]:
    payload = task.get("payload") if isinstance(task.get("payload"), Mapping) else {}
    requested = [
        flag
        for flag in (
            "domain_truth_write",
            "artifact_gate_override",
            "study_truth_write",
            "publication_quality_verdict",
            "current_package_write",
            "memory_body_write",
            "publication_route_memory_writeback_accept",
            "memory_write_router_accept",
        )
        if bool(payload.get(flag))
    ]
    payload_writes = payload.get("requested_writes")
    if isinstance(payload_writes, list):
        requested.extend(str(item) for item in payload_writes if str(item or "").strip())
    return list(dict.fromkeys(requested))


def build_forbidden_write_guard_proof(
    *,
    result: str,
    task_id: str | None,
    task_kind: str | None,
    requested_writes: Iterable[str],
) -> dict[str, Any]:
    requested = [str(item) for item in requested_writes if str(item or "").strip()]
    return {
        "surface_kind": "mas_opl_forbidden_write_guard_proof",
        "version": "mas-opl-forbidden-write-guard.v1",
        "target_domain_id": TARGET_DOMAIN_ID,
        "task_id": task_id,
        "task_kind": task_kind,
        "result": result,
        "guard_mode": "fail_closed",
        "guard_owner": DOMAIN_OWNER,
        "requested_writes": requested,
        "forbidden_requested_writes": [
            item for item in requested if item in FORBIDDEN_AUTHORITY_WRITES
        ],
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
        "can_write_domain_truth": False,
        "can_authorize_publication_quality": False,
        "can_override_artifact_gate": False,
        "can_write_current_package": False,
        "proof_refs": [
            {
                "ref_kind": "python_symbol",
                "ref": (
                    "med_autoscience.controllers.owner_route_handoff."
                    "dispatch_orchestration.dispatch_family_domain_handler_task"
                ),
                "role": "dispatch_guard",
            },
            {
                "ref_kind": "json_pointer",
                "ref": "/authority_boundary/forbidden_authorities",
                "role": "receipt_authority_boundary",
            },
        ],
    }


__all__ = [
    "FORBIDDEN_AUTHORITY_WRITES",
    "build_forbidden_write_guard_proof",
    "requested_writes_from_task",
]
