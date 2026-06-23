from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


CLOSEOUT_RELATIVE_ROOTS = (
    Path("artifacts/supervision/consumer/default_executor_execution"),
    Path("artifacts/supervision/consumer/stage_attempt_closeouts"),
)
TERMINAL_READBACK_STATUS = "opl_runtime_terminal_readback_observed"
WAITING_READBACK_STATUS = "waiting_for_opl_runtime_live_readback"


def paper_mission_opl_runtime_carrier_readback(
    *,
    carrier: Mapping[str, Any],
    study_root: Path,
) -> dict[str, Any]:
    matched = _matching_terminal_closeout(carrier=carrier, study_root=study_root)
    if matched is None:
        return {
            "surface_kind": "paper_mission_opl_runtime_carrier_readback",
            "schema_version": 1,
            "carrier_status": WAITING_READBACK_STATUS,
            "runtime_readback_status": "missing",
            "dispatch_status": _text(carrier.get("dispatch_status"))
            or "transition_request_pending",
            "domain_ready_verdict": "opl_runtime_readback_missing",
            "provider_completion_is_domain_completion": False,
            "provider_completion_is_domain_ready": False,
            "can_claim_provider_running": False,
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
            "authority_materialized": False,
            "request_carrier_preserved": True,
        }

    closeout, closeout_ref = matched
    return {
        "surface_kind": "paper_mission_opl_runtime_carrier_readback",
        "schema_version": 1,
        "carrier_status": TERMINAL_READBACK_STATUS,
        "runtime_readback_status": "terminal_closeout_observed",
        "dispatch_status": "terminal_closeout_observed",
        "domain_ready_verdict": "domain_gate_pending",
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "can_claim_provider_running": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_materialized": False,
        "request_carrier_preserved": True,
        "terminal_closeout": _terminal_closeout_readback(
            closeout=closeout,
            closeout_ref=closeout_ref,
        ),
    }


def attach_opl_runtime_carrier_readback(
    *,
    readback: Mapping[str, Any],
    study_root: Path,
) -> dict[str, Any]:
    result = dict(readback)
    carrier = _mapping(result.get("opl_runtime_carrier"))
    if not carrier:
        return result
    carrier_readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
    )
    result["opl_runtime_carrier_readback"] = carrier_readback
    result["opl_runtime_readback_status"] = carrier_readback["carrier_status"]
    return result


def _matching_terminal_closeout(
    *,
    carrier: Mapping[str, Any],
    study_root: Path,
) -> tuple[dict[str, Any], str] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    matches: list[tuple[float, dict[str, Any], str]] = []
    for root_ref in CLOSEOUT_RELATIVE_ROOTS:
        closeout_root = resolved_study_root / root_ref
        if not closeout_root.is_dir():
            continue
        for closeout_path in closeout_root.glob("*.json"):
            closeout = _read_json_object(closeout_path)
            if closeout is None:
                continue
            if not _matches_carrier(closeout=closeout, carrier=carrier):
                continue
            matches.append(
                (
                    closeout_path.stat().st_mtime,
                    closeout,
                    _study_relative_ref(
                        study_root=resolved_study_root,
                        path=closeout_path,
                    ),
                )
            )
    if not matches:
        return None
    _mtime, closeout, closeout_ref = sorted(
        matches,
        key=lambda item: item[0],
        reverse=True,
    )[0]
    return closeout, closeout_ref


def _matches_carrier(
    *,
    closeout: Mapping[str, Any],
    carrier: Mapping[str, Any],
) -> bool:
    if _text(closeout.get("surface_kind")) != "stage_attempt_closeout_packet":
        return False
    if _text(closeout.get("study_id")) != _text(carrier.get("study_id")):
        return False
    if _text(closeout.get("work_unit_id")) != _text(carrier.get("work_unit_id")):
        return False
    if _text(closeout.get("work_unit_fingerprint")) != _text(
        carrier.get("work_unit_fingerprint")
    ):
        return False
    route_target = _carrier_route_target(carrier)
    if route_target is not None and _text(closeout.get("stage_id")) != route_target:
        return False
    if closeout.get("provider_completion_is_domain_completion") is True:
        return False
    if closeout.get("provider_completion_is_domain_ready") is True:
        return False
    if closeout.get("domain_completion_claimed") is True:
        return False
    if closeout.get("domain_ready_claimed") is True:
        return False
    boundary = _mapping(closeout.get("authority_boundary"))
    return boundary.get("record_only_surface") is True


def _carrier_route_target(carrier: Mapping[str, Any]) -> str | None:
    command_kind = _text(carrier.get("command_kind"))
    route_target = _text(carrier.get("route_target"))
    route = _mapping(carrier.get("opl_route_command"))
    command_kind = command_kind or _text(route.get("command_kind"))
    route_target = route_target or _text(route.get("target"))
    if command_kind in {"start_next_stage", "resume_stage", "route_back"}:
        return route_target
    return None


def _terminal_closeout_readback(
    *,
    closeout: Mapping[str, Any],
    closeout_ref: str,
) -> dict[str, Any]:
    return {
        "surface_kind": _text(closeout.get("surface_kind")),
        "closeout_ref": closeout_ref,
        "status": _text(closeout.get("status")),
        "study_id": _text(closeout.get("study_id")),
        "stage_id": _text(closeout.get("stage_id")),
        "stage_attempt_id": _text(closeout.get("stage_attempt_id")),
        "work_unit_id": _text(closeout.get("work_unit_id")),
        "work_unit_fingerprint": _text(closeout.get("work_unit_fingerprint")),
        "stage_packet_ref": _text(closeout.get("stage_packet_ref")),
        "provider_attempt_ref": _text(closeout.get("provider_attempt_ref")),
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "domain_completion_claimed": False,
        "domain_ready_claimed": False,
        "typed_blocker_ref": _text(closeout.get("typed_blocker_ref")),
        "blocked_reason": _text(closeout.get("blocked_reason")),
        "closeout_refs": _text_list(closeout.get("closeout_refs")),
        "authority_boundary": {
            "record_only_surface": True,
            "provider_completion_is_domain_completion": False,
            "artifact_mutation_authorized": False,
            "publication_eval_latest_write_authorized": False,
            "controller_decision_write_authorized": False,
        },
    }


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _study_relative_ref(*, study_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(study_root.resolve()))
    except ValueError:
        return str(path.resolve())


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list | tuple):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "TERMINAL_READBACK_STATUS",
    "WAITING_READBACK_STATUS",
    "attach_opl_runtime_carrier_readback",
    "paper_mission_opl_runtime_carrier_readback",
]
