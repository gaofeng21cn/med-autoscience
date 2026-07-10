from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.domain_route_profile import (
    DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
)


IMMUTABLE_PACKET_DIRNAME = "immutable"
OPL_STAGE_ATTEMPT_CARRIER_BOUNDARY = {
    "surface_kind": "opl_stage_attempt_carrier_packet_boundary",
    "active_caller_class": "abi_provenance_carrier_only",
    "allowed_reference_class": "retired_handoff_provenance",
    "diagnostic_role": "retired_default_paper_dispatch",
    "replacement_task_kind": DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND,
    "ordinary_schedulable": False,
    "default_paper_mission_entry": False,
    "migration_diagnostic_only": True,
    "can_select_next_paper_stage": False,
    "can_authorize_provider_admission": False,
    "counts_as_paper_progress": False,
    "can_claim_runtime_ready": False,
    "can_claim_publication_ready": False,
    "forbidden_claims": [
        "paper_progress",
        "publication_ready",
        "submission_ready",
        "runtime_ready",
        "provider_running",
        "owner_receipt_written",
        "typed_blocker_written",
        "human_gate_written",
        "current_package",
    ],
    "dispatch_fail_closed_reason": "opl_stage_attempt_carrier_not_schedulable",
}


def immutable_dispatch_packet_path(
    *,
    dispatch_path: Path,
    dispatch: Mapping[str, Any],
) -> Path:
    action_type = _slug(_text(dispatch.get("action_type")) or dispatch_path.stem)
    fingerprint = _packet_fingerprint(dispatch=dispatch, dispatch_path=dispatch_path)
    return dispatch_path.parent / IMMUTABLE_PACKET_DIRNAME / action_type / f"{fingerprint}.json"


def dispatch_stage_packet_path(dispatch: Mapping[str, Any], *, fallback_dispatch_path: Path) -> Path:
    refs = _mapping(dispatch.get("refs"))
    packet_path = _text(refs.get("immutable_dispatch_path")) or _text(refs.get("stage_packet_path"))
    if packet_path is None:
        return fallback_dispatch_path
    return Path(packet_path)


def dispatch_with_immutable_packet_ref(
    *,
    dispatch: Mapping[str, Any],
    dispatch_path: Path,
) -> dict[str, Any]:
    packet_path = immutable_dispatch_packet_path(dispatch_path=dispatch_path, dispatch=dispatch)
    payload = dict(dispatch)
    refs = {**_mapping(payload.get("refs"))}
    refs["dispatch_path"] = str(dispatch_path)
    refs["immutable_dispatch_path"] = str(packet_path)
    refs["stage_packet_path"] = str(packet_path)
    payload["refs"] = refs
    payload["opl_stage_attempt_carrier_boundary"] = dict(OPL_STAGE_ATTEMPT_CARRIER_BOUNDARY)
    payload["active_caller_class"] = "abi_provenance_carrier_only"
    payload["allowed_reference_class"] = "retired_handoff_provenance"
    payload["diagnostic_role"] = "retired_default_paper_dispatch"
    payload["replacement_task_kind"] = DOMAIN_ROUTE_START_OR_RESUME_TASK_KIND
    payload["ordinary_schedulable"] = False
    payload["default_paper_mission_entry"] = False
    payload["migration_diagnostic_only"] = True
    payload["can_select_next_paper_stage"] = False
    payload["can_authorize_provider_admission"] = False
    payload["counts_as_paper_progress"] = False
    payload["can_claim_runtime_ready"] = False
    payload["can_claim_publication_ready"] = False
    payload["forbidden_claims"] = list(OPL_STAGE_ATTEMPT_CARRIER_BOUNDARY["forbidden_claims"])
    return payload


def _packet_fingerprint(*, dispatch: Mapping[str, Any], dispatch_path: Path) -> str:
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(
        _mapping(dispatch.get("prompt_contract")).get("owner_route")
    )
    source_refs = _mapping(owner_route.get("source_refs"))
    identity = {
        "dispatch_path": str(dispatch_path),
        "action_type": _text(dispatch.get("action_type")),
        "dispatch_authority": _text(dispatch.get("dispatch_authority")),
        "idempotency_key": _text(dispatch.get("idempotency_key")) or _text(owner_route.get("idempotency_key")),
        "work_unit_id": _text(source_refs.get("work_unit_id")) or _text(owner_route.get("work_unit_id")),
        "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint"))
        or _text(source_refs.get("work_unit_fingerprint"))
        or _text(dispatch.get("action_fingerprint")),
        "runtime_health_epoch": _text(owner_route.get("runtime_health_epoch"))
        or _text(source_refs.get("runtime_health_epoch")),
        "generated_at": _text(dispatch.get("generated_at")),
    }
    rendered = json.dumps(identity, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()[:24]


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "dispatch"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = [
    "IMMUTABLE_PACKET_DIRNAME",
    "OPL_STAGE_ATTEMPT_CARRIER_BOUNDARY",
    "dispatch_stage_packet_path",
    "dispatch_with_immutable_packet_ref",
    "immutable_dispatch_packet_path",
]
