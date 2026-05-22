from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping, Sequence

from . import report_store


class DomainHealthDiagnosticControllerAction(StrEnum):
    CLEAR = "clear"
    APPLIED = "applied"
    SUPPRESSED = "suppressed"


@dataclass(frozen=True)
class DomainHealthDiagnosticControllerState:
    last_seen_fingerprint: str | None = None
    last_applied_fingerprint: str | None = None
    last_applied_at: str | None = None
    last_status: str | None = None
    last_suppression_reason: str | None = None

    @classmethod
    def from_payload(cls, payload: object | None = None) -> "DomainHealthDiagnosticControllerState":
        if payload is None:
            return cls()
        if isinstance(payload, cls):
            return payload
        if not isinstance(payload, Mapping):
            raise TypeError("domain health diagnostic controller state payload must be a mapping")
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
class DomainHealthDiagnosticState:
    schema_version: int = 1
    updated_at: str | None = None
    controllers: dict[str, DomainHealthDiagnosticControllerState] = field(default_factory=dict)

    @classmethod
    def from_payload(cls, payload: object | None = None) -> "DomainHealthDiagnosticState":
        if payload is None:
            return cls()
        if isinstance(payload, cls):
            return payload
        if not isinstance(payload, Mapping):
            raise TypeError("domain health diagnostic state payload must be a mapping")
        raw_controllers = payload.get("controllers") or {}
        if not isinstance(raw_controllers, Mapping):
            raise TypeError("domain health diagnostic state controllers must be a mapping")
        controllers = {
            _require_text("controller name", name): DomainHealthDiagnosticControllerState.from_payload(value)
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
class DomainHealthDiagnosticInterventionPlan:
    action: DomainHealthDiagnosticControllerAction
    should_apply: bool
    suppression_reason: str | None
    controller_state: DomainHealthDiagnosticControllerState

    def __post_init__(self) -> None:
        if not isinstance(self.action, DomainHealthDiagnosticControllerAction):
            object.__setattr__(self, "action", DomainHealthDiagnosticControllerAction(self.action))
        if not isinstance(self.should_apply, bool):
            raise TypeError("should_apply must be bool")
        if not isinstance(self.controller_state, DomainHealthDiagnosticControllerState):
            object.__setattr__(self, "controller_state", DomainHealthDiagnosticControllerState.from_payload(self.controller_state))
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


def load_domain_health_diagnostic_state(quest_root: Path) -> DomainHealthDiagnosticState:
    payload = report_store.load_domain_health_diagnostic_state(quest_root)
    return DomainHealthDiagnosticState.from_payload(payload)


def save_domain_health_diagnostic_state(quest_root: Path, payload: DomainHealthDiagnosticState) -> None:
    if not isinstance(payload, DomainHealthDiagnosticState):
        raise TypeError("payload must be DomainHealthDiagnosticState")
    report_store.save_domain_health_diagnostic_state(quest_root, payload.to_dict())


def write_domain_health_diagnostic_report(*, quest_root: Path, report: Mapping[str, Any], markdown: str) -> tuple[Path, Path]:
    scanned_at = _require_text("report.scanned_at", report.get("scanned_at"))
    return report_store.write_timestamped_report(
        quest_root=quest_root,
        report_group="domain_health_diagnostic",
        timestamp=scanned_at,
        report=report,
        markdown=markdown,
    )


def plan_controller_intervention(
    *,
    previous_controller_state: DomainHealthDiagnosticControllerState,
    dry_run_result: Mapping[str, Any],
    fingerprint: str,
    apply: bool,
    scanned_at: str,
    intervention_statuses: Sequence[str],
) -> DomainHealthDiagnosticInterventionPlan:
    if not isinstance(previous_controller_state, DomainHealthDiagnosticControllerState):
        raise TypeError("previous_controller_state must be DomainHealthDiagnosticControllerState")
    status = _optional_text(dry_run_result.get("status"))
    suppression_reason = _optional_text(dry_run_result.get("suppression_reason"))
    action = DomainHealthDiagnosticControllerAction.CLEAR
    should_apply = False
    if status in intervention_statuses:
        seen_before = previous_controller_state.last_applied_fingerprint == fingerprint
        should_apply = apply and not seen_before
        if should_apply:
            action = DomainHealthDiagnosticControllerAction.APPLIED
            suppression_reason = None
        else:
            action = DomainHealthDiagnosticControllerAction.SUPPRESSED
            suppression_reason = "duplicate_fingerprint" if apply else "apply_disabled"

    controller_state = DomainHealthDiagnosticControllerState(
        last_seen_fingerprint=fingerprint,
        last_applied_fingerprint=(
            fingerprint
            if action is DomainHealthDiagnosticControllerAction.APPLIED
            else previous_controller_state.last_applied_fingerprint
        ),
        last_applied_at=scanned_at if action is DomainHealthDiagnosticControllerAction.APPLIED else previous_controller_state.last_applied_at,
        last_status=status,
        last_suppression_reason=suppression_reason,
    )
    return DomainHealthDiagnosticInterventionPlan(
        action=action,
        should_apply=should_apply,
        suppression_reason=suppression_reason,
        controller_state=controller_state,
    )
