from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import report_store


class RuntimeWatchControllerAction(StrEnum):
    CLEAR = "clear"
    APPLIED = "applied"
    SUPPRESSED = "suppressed"


@dataclass(frozen=True)
class RuntimeWatchControllerState:
    last_seen_fingerprint: str | None = None
    last_applied_fingerprint: str | None = None
    last_applied_at: str | None = None
    last_status: str | None = None
    last_suppression_reason: str | None = None

    @classmethod
    def from_payload(cls, payload: object | None = None) -> "RuntimeWatchControllerState":
        if payload is None:
            return cls()
        if isinstance(payload, cls):
            return payload
        if not isinstance(payload, Mapping):
            raise TypeError("runtime watch controller state payload must be a mapping")
        return cls(
            last_seen_fingerprint=_optional_text(payload.get("last_seen_fingerprint")),
            last_applied_fingerprint=_optional_text(payload.get("last_applied_fingerprint")),
            last_applied_at=_optional_text(payload.get("last_applied_at")),
            last_status=_optional_text(payload.get("last_status")),
            last_suppression_reason=_optional_text(payload.get("last_suppression_reason")),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "last_seen_fingerprint": self.last_seen_fingerprint,
            "last_applied_fingerprint": self.last_applied_fingerprint,
            "last_applied_at": self.last_applied_at,
            "last_status": self.last_status,
            "last_suppression_reason": self.last_suppression_reason,
        }


@dataclass(frozen=True)
class RuntimeWatchState:
    schema_version: int = 1
    updated_at: str | None = None
    controllers: dict[str, RuntimeWatchControllerState] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: object | None = None) -> "RuntimeWatchState":
        if payload is None:
            return cls()
        if isinstance(payload, cls):
            return payload
        if not isinstance(payload, Mapping):
            raise TypeError("runtime watch state payload must be a mapping")
        raw_controllers = payload.get("controllers") or {}
        if not isinstance(raw_controllers, Mapping):
            raise TypeError("runtime watch state controllers must be a mapping")
        controllers = {
            _require_text("controller name", name): RuntimeWatchControllerState.from_payload(value)
            for name, value in raw_controllers.items()
        }
        return cls(
            schema_version=int(payload.get("schema_version") or 1),
            updated_at=_optional_text(payload.get("updated_at")),
            controllers=controllers,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "updated_at": self.updated_at,
            "controllers": {
                name: controller_state.to_dict()
                for name, controller_state in self.controllers.items()
            },
        }


@dataclass(frozen=True)
class RuntimeWatchInterventionPlan:
    action: RuntimeWatchControllerAction
    should_apply: bool
    suppression_reason: str | None
    controller_state: RuntimeWatchControllerState

    def __post_init__(self) -> None:
        if not isinstance(self.action, RuntimeWatchControllerAction):
            object.__setattr__(self, "action", RuntimeWatchControllerAction(self.action))
        if not isinstance(self.should_apply, bool):
            raise TypeError("should_apply must be bool")
        if not isinstance(self.controller_state, RuntimeWatchControllerState):
            object.__setattr__(self, "controller_state", RuntimeWatchControllerState.from_payload(self.controller_state))
        object.__setattr__(self, "suppression_reason", _optional_text(self.suppression_reason))


def _require_text(label: str, value: object) -> str:
    if not isinstance(value, str) or not value:
        raise TypeError(f"{label} must be a non-empty string")
    return value


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError("value must be str or None")
    stripped = value.strip()
    return stripped or None


def load_watch_state(quest_root: Path) -> RuntimeWatchState:
    payload = report_store.load_watch_state(quest_root)
    return RuntimeWatchState.from_payload(payload)


def save_watch_state(quest_root: Path, payload: RuntimeWatchState) -> None:
    if not isinstance(payload, RuntimeWatchState):
        raise TypeError("payload must be RuntimeWatchState")
    report_store.save_watch_state(quest_root, payload.to_dict())


def write_watch_report(*, quest_root: Path, report: Mapping[str, Any], markdown: str) -> tuple[Path, Path]:
    scanned_at = _require_text("report.scanned_at", report.get("scanned_at"))
    return report_store.write_timestamped_report(
        quest_root=quest_root,
        report_group="runtime_watch",
        timestamp=scanned_at,
        report=report,
        markdown=markdown,
    )


def plan_controller_intervention(
    *,
    previous_controller_state: RuntimeWatchControllerState,
    dry_run_result: Mapping[str, Any],
    fingerprint: str,
    apply: bool,
    scanned_at: str,
    intervention_statuses: Sequence[str],
) -> RuntimeWatchInterventionPlan:
    if not isinstance(previous_controller_state, RuntimeWatchControllerState):
        raise TypeError("previous_controller_state must be RuntimeWatchControllerState")
    status = _optional_text(dry_run_result.get("status"))
    suppression_reason = _optional_text(dry_run_result.get("suppression_reason"))
    action = RuntimeWatchControllerAction.CLEAR
    should_apply = False
    if status in intervention_statuses:
        seen_before = previous_controller_state.last_applied_fingerprint == fingerprint
        should_apply = apply and not seen_before
        if should_apply:
            action = RuntimeWatchControllerAction.APPLIED
            suppression_reason = None
        else:
            action = RuntimeWatchControllerAction.SUPPRESSED
            suppression_reason = "duplicate_fingerprint" if apply else "apply_disabled"

    controller_state = RuntimeWatchControllerState(
        last_seen_fingerprint=fingerprint,
        last_applied_fingerprint=(
            fingerprint
            if action is RuntimeWatchControllerAction.APPLIED
            else previous_controller_state.last_applied_fingerprint
        ),
        last_applied_at=scanned_at if action is RuntimeWatchControllerAction.APPLIED else previous_controller_state.last_applied_at,
        last_status=status,
        last_suppression_reason=suppression_reason,
    )
    return RuntimeWatchInterventionPlan(
        action=action,
        should_apply=should_apply,
        suppression_reason=suppression_reason,
        controller_state=controller_state,
    )
