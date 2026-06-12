from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Mapping

from med_autoscience.controllers import publication_work_units


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _sorted_texts(values: object) -> tuple[str, ...]:
    if not isinstance(values, list | tuple | set):
        return ()
    return tuple(sorted({text for item in values if (text := _text(item))}))


def _digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


def stable_current_owner_ticket_fingerprint(
    *,
    study_id: str | None,
    work_unit_id: str | None,
    action_type: str | None,
) -> str | None:
    if study_id is None or work_unit_id is None or action_type is None:
        return None
    return f"study-progress-current-owner-ticket::{study_id}::{work_unit_id}::{action_type}"


def stable_route_currentness_fingerprint(
    *,
    study_id: str | None,
    source: str | None,
    work_unit_id: str | None,
    action_type: str | None,
    next_owner: str | None = None,
    source_eval_id: str | None = None,
    target_surface_ref: str | None = None,
    required_delta_kind: str | None = None,
) -> str | None:
    if source is None or work_unit_id is None or action_type is None:
        return None
    digest = _digest(
        {
            "action_type": action_type,
            "next_owner": next_owner,
            "required_delta_kind": required_delta_kind,
            "source": source,
            "source_eval_id": source_eval_id,
            "study_id": study_id,
            "target_surface_ref": target_surface_ref,
            "work_unit_id": work_unit_id,
        }
    )
    return f"route-currentness::{study_id or 'unknown-study'}::{digest}"


def is_synthetic_current_owner_ticket(value: object) -> bool:
    text = _text(value)
    return text is not None and text.startswith("study-progress-current-owner-ticket::")


@dataclass(frozen=True)
class ControlWorkUnitIdentity:
    domain: str
    study_id: str
    quest_id: str | None
    lane: str
    unit_id: str
    action_type: str
    effective_blockers: tuple[str, ...]
    idempotency_scope: str = "work_unit"
    fingerprint_override: str | None = None

    @property
    def fingerprint(self) -> str:
        if self.fingerprint_override:
            return self.fingerprint_override
        digest = _digest(
            {
                "domain": self.domain,
                "lane": self.lane,
                "unit_id": self.unit_id,
                "action_type": self.action_type,
                "effective_blockers": self.effective_blockers,
                "idempotency_scope": self.idempotency_scope,
            }
        )
        return f"{self.domain}::{digest}"

    @property
    def dispatch_key(self) -> str:
        return f"{self.fingerprint}::{self.unit_id}::{self.action_type}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain": self.domain,
            "study_id": self.study_id,
            "quest_id": self.quest_id,
            "lane": self.lane,
            "unit_id": self.unit_id,
            "action_type": self.action_type,
            "effective_blockers": list(self.effective_blockers),
            "idempotency_scope": self.idempotency_scope,
            "fingerprint_override": self.fingerprint_override,
            "fingerprint": self.fingerprint,
            "dispatch_key": self.dispatch_key,
        }


def publication_work_unit_identity(
    *,
    study_id: str,
    quest_id: str | None,
    blockers: object,
    next_work_unit: Mapping[str, Any],
    action_type: str,
) -> ControlWorkUnitIdentity:
    unit_id = _text(next_work_unit.get("unit_id"))
    lane = _text(next_work_unit.get("lane"))
    normalized_blockers = _sorted_texts(blockers)
    if unit_id is None or lane is None:
        raise ValueError("publication work unit identity requires unit_id and lane")
    effective_blockers = publication_work_units.fingerprint_blockers_for_work_unit(
        blockers=normalized_blockers,
        next_work_unit=next_work_unit,
    )
    return ControlWorkUnitIdentity(
        domain="publication-work-unit",
        study_id=study_id,
        quest_id=quest_id,
        lane=lane,
        unit_id=unit_id,
        action_type=action_type,
        effective_blockers=tuple(effective_blockers),
    )
