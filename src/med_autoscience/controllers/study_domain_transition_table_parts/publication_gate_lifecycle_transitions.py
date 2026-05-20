from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import publication_work_unit_lifecycle


PUBLICATION_WORK_UNIT_LIFECYCLE_RELATIVE_PATH = Path(
    "artifacts/controller/publication_work_unit_lifecycle/latest.json"
)


def project_transition(
    *,
    study_id: str,
    lifecycle: Mapping[str, Any],
    lifecycle_ref: str | None,
    source_refs: Iterable[str],
    completion_receipt_consumption: Mapping[str, Any],
) -> dict[str, Any] | None:
    payload = dict(lifecycle) if isinstance(lifecycle, Mapping) else {}
    if not payload:
        return None
    if not publication_work_unit_lifecycle.lifecycle_payload_is_closed(payload):
        return None
    if _text(payload.get("recommended_next_route")) != "return_to_publication_gate_recheck":
        return None
    if _text(payload.get("next_owner")) != "publication_gate":
        return None
    work_unit = _compact_lifecycle_work_unit(payload.get("work_unit"))
    next_work_unit: dict[str, Any] = {
        "unit_id": "publication_gate_recheck",
        "lane": "review",
        "summary": "Replay the publication gate for the closed controller work unit.",
    }
    if work_unit:
        next_work_unit["source_work_unit"] = work_unit
    return _transition(
        study_id=study_id,
        decision_type="publication_gate_blocker",
        route_target="review",
        next_work_unit=next_work_unit,
        controller_action="run_gate_clearing_batch",
        owner="publication_gate",
        typed_blocker=_typed_blocker(
            blocker_id="publication_gate_recheck_required",
            blocker_type="publication_gate",
            summary="A closed controller work unit has handed off to the publication gate for replay.",
            required_owner_surface=lifecycle_ref or str(PUBLICATION_WORK_UNIT_LIFECYCLE_RELATIVE_PATH),
        ),
        guard_boundary=_guard_boundary(
            required_owner_surface=lifecycle_ref or str(PUBLICATION_WORK_UNIT_LIFECYCLE_RELATIVE_PATH),
        ),
        source_refs=source_refs,
        completion_receipt_consumption=completion_receipt_consumption,
    )


def _transition(
    *,
    study_id: str,
    decision_type: str,
    route_target: str,
    next_work_unit: Mapping[str, Any],
    controller_action: str,
    owner: str,
    typed_blocker: Mapping[str, Any] | None,
    guard_boundary: Mapping[str, Any],
    source_refs: Iterable[str],
    completion_receipt_consumption: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "study_id": study_id,
        "decision_type": decision_type,
        "route_target": route_target,
        "next_work_unit": dict(next_work_unit),
        "controller_action": controller_action,
        "owner": owner,
        "typed_blocker": dict(typed_blocker) if typed_blocker else None,
        "guard_boundary": dict(guard_boundary),
        "source_refs": list(source_refs),
    }
    if completion_receipt_consumption:
        payload["completion_receipt_consumption"] = dict(completion_receipt_consumption)
    return payload


def _typed_blocker(
    *,
    blocker_id: str,
    blocker_type: str,
    summary: str,
    required_owner_surface: str,
) -> dict[str, Any]:
    return {
        "blocker_id": blocker_id,
        "blocker_type": blocker_type,
        "summary": summary,
        "required_owner_surface": required_owner_surface,
        "write_permitted": False,
    }


def _guard_boundary(*, required_owner_surface: str) -> dict[str, Any]:
    return {
        "runner_boundary": "mas_domain_read_model_only",
        "can_write_domain_truth": False,
        "can_execute_generic_state_machine": False,
        "opl_generic_runner_may_resume": False,
        "mas_owner_apply_receipt_required": False,
        "required_owner_surface": required_owner_surface,
    }


def _compact_lifecycle_work_unit(value: object) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    unit_id = _text(value.get("unit_id"))
    if not unit_id:
        return None
    payload: dict[str, Any] = {"unit_id": unit_id}
    for key in ("lane", "summary", "fingerprint", "status", "lifecycle_status"):
        text = _text(value.get(key))
        if text:
            payload[key] = text
    return payload


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = ["PUBLICATION_WORK_UNIT_LIFECYCLE_RELATIVE_PATH", "project_transition"]
