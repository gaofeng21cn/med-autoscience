from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from med_autoscience.runtime_escalation_record import RuntimeEscalationRecordRef


_RECORD_ALLOWED_FIELDS = frozenset(
    {
        "schema_version",
        "decision_id",
        "study_id",
        "quest_id",
        "emitted_at",
        "decision_type",
        "charter_ref",
        "runtime_escalation_ref",
        "publication_eval_ref",
        "requires_human_confirmation",
        "controller_actions",
        "reason",
        "route_target",
        "route_key_question",
        "route_rationale",
        "family_event_envelope",
        "family_checkpoint_lineage",
        "family_human_gates",
        "artifact_path",
    }
)
_CHARTER_REF_ALLOWED_FIELDS = frozenset({"charter_id", "artifact_path"})
_PUBLICATION_EVAL_REF_ALLOWED_FIELDS = frozenset({"eval_id", "artifact_path"})
_CONTROLLER_ACTION_ALLOWED_FIELDS = frozenset({"action_type", "payload_ref"})
_RECORD_REF_ALLOWED_FIELDS = frozenset({"decision_id", "artifact_path"})


class StudyDecisionType(StrEnum):
    CONTINUE_SAME_LINE = "continue_same_line"
    ROUTE_BACK_SAME_LINE = "route_back_same_line"
    BOUNDED_ANALYSIS = "bounded_analysis"
    RELAUNCH_BRANCH = "relaunch_branch"
    REROUTE_STUDY = "reroute_study"
    STOP_LOSS = "stop_loss"
    PROMOTE_TO_DELIVERY = "promote_to_delivery"


class StudyDecisionActionType(StrEnum):
    ENSURE_STUDY_RUNTIME = "ensure_study_runtime"
    ENSURE_STUDY_RUNTIME_RELAUNCH_STOPPED = "ensure_study_runtime_relaunch_stopped"
    PAUSE_RUNTIME = "pause_runtime"
    STOP_RUNTIME = "stop_runtime"


def _reject_unknown_fields(label: str, payload: dict[str, Any], allowed_fields: frozenset[str]) -> None:
    unknown_fields = sorted(set(payload) - allowed_fields)
    if unknown_fields:
        raise ValueError(f"{label} payload contains unknown fields: {', '.join(unknown_fields)}")


def _require_text(label: str, field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} {field_name} must be non-empty")
    return value.strip()


def _normalize_decision_type(value: Any) -> StudyDecisionType:
    normalized = _require_text("study decision record", "decision_type", value)
    try:
        return StudyDecisionType(normalized)
    except ValueError as exc:
        raise ValueError(f"unknown study decision type: {normalized}") from exc


def _normalize_controller_action_type(value: Any) -> StudyDecisionActionType:
    normalized = _require_text("study decision controller action", "action_type", value)
    try:
        return StudyDecisionActionType(normalized)
    except ValueError as exc:
        raise ValueError(f"unknown study decision controller action: {normalized}") from exc


def _payload_text(payload: dict[str, Any], field_name: str, label: str) -> str:
    if field_name not in payload:
        raise ValueError(f"{label} payload missing {field_name}")
    return _require_text(label, field_name, payload.get(field_name))


def _payload_int(payload: dict[str, Any], field_name: str, label: str) -> int:
    if field_name not in payload:
        raise ValueError(f"{label} payload missing {field_name}")
    value = payload.get(field_name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{label} {field_name} must be int")
    return value


def _payload_bool(payload: dict[str, Any], field_name: str, label: str) -> bool:
    if field_name not in payload:
        raise ValueError(f"{label} payload missing {field_name}")
    value = payload.get(field_name)
    if not isinstance(value, bool):
        raise TypeError(f"{label} {field_name} must be bool")
    return value


def _optional_payload_text(payload: dict[str, Any], field_name: str) -> str | None:
    if field_name not in payload:
        return None
    value = payload.get(field_name)
    if value is None:
        return None
    return _require_text("study decision record", field_name, value)


def _payload_mapping(payload: dict[str, Any], field_name: str, label: str) -> dict[str, Any]:
    if field_name not in payload:
        raise ValueError(f"{label} payload missing {field_name}")
    raw_value = payload.get(field_name)
    if not isinstance(raw_value, dict):
        raise ValueError(f"{label} {field_name} must be a mapping")
    return raw_value


def _payload_object_sequence(payload: dict[str, Any], field_name: str, label: str) -> list[dict[str, Any]]:
    if field_name not in payload:
        raise ValueError(f"{label} payload missing {field_name}")
    raw_value = payload.get(field_name)
    if not isinstance(raw_value, list):
        raise ValueError(f"{label} {field_name} must be a list")
    if not raw_value:
        raise ValueError(f"{label} {field_name} must not be empty")
    for item in raw_value:
        if not isinstance(item, dict):
            raise ValueError(f"{label} {field_name} entries must be mappings")
    return raw_value


def _optional_payload_mapping(payload: dict[str, Any], field_name: str, label: str) -> dict[str, Any] | None:
    if field_name not in payload:
        return None
    raw_value = payload.get(field_name)
    if raw_value is None:
        return None
    if not isinstance(raw_value, dict):
        raise ValueError(f"{label} {field_name} must be a mapping when provided")
    return dict(raw_value)


def _optional_payload_mapping_sequence(
    payload: dict[str, Any],
    field_name: str,
    label: str,
) -> tuple[dict[str, Any], ...]:
    if field_name not in payload:
        return ()
    raw_value = payload.get(field_name)
    if raw_value is None:
        return ()
    if not isinstance(raw_value, list):
        raise ValueError(f"{label} {field_name} must be a list when provided")
    normalized: list[dict[str, Any]] = []
    for item in raw_value:
        if not isinstance(item, dict):
            raise ValueError(f"{label} {field_name} entries must be mappings")
        normalized.append(dict(item))
    return tuple(normalized)


@dataclass(frozen=True)
class StudyDecisionCharterRef:
    charter_id: str
    artifact_path: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "charter_id", _require_text("study decision charter ref", "charter_id", self.charter_id))
        object.__setattr__(self, "artifact_path", _require_text("study decision charter ref", "artifact_path", self.artifact_path))

    def to_dict(self) -> dict[str, str]:
        return {
            "charter_id": self.charter_id,
            "artifact_path": self.artifact_path,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyDecisionCharterRef":
        if not isinstance(payload, dict):
            raise TypeError("study decision charter ref payload must be a mapping")
        _reject_unknown_fields("study decision charter ref", payload, _CHARTER_REF_ALLOWED_FIELDS)
        return cls(
            charter_id=_payload_text(payload, "charter_id", "study decision charter ref"),
            artifact_path=_payload_text(payload, "artifact_path", "study decision charter ref"),
        )


@dataclass(frozen=True)
class StudyDecisionPublicationEvalRef:
    eval_id: str
    artifact_path: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "eval_id", _require_text("study decision publication eval ref", "eval_id", self.eval_id))
        object.__setattr__(self, "artifact_path", _require_text("study decision publication eval ref", "artifact_path", self.artifact_path))

    def to_dict(self) -> dict[str, str]:
        return {
            "eval_id": self.eval_id,
            "artifact_path": self.artifact_path,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyDecisionPublicationEvalRef":
        if not isinstance(payload, dict):
            raise TypeError("study decision publication eval ref payload must be a mapping")
        _reject_unknown_fields("study decision publication eval ref", payload, _PUBLICATION_EVAL_REF_ALLOWED_FIELDS)
        return cls(
            eval_id=_payload_text(payload, "eval_id", "study decision publication eval ref"),
            artifact_path=_payload_text(payload, "artifact_path", "study decision publication eval ref"),
        )


@dataclass(frozen=True)
class StudyDecisionControllerAction:
    action_type: StudyDecisionActionType | str
    payload_ref: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "action_type", _normalize_controller_action_type(self.action_type))
        object.__setattr__(self, "payload_ref", _require_text("study decision controller action", "payload_ref", self.payload_ref))

    def to_dict(self) -> dict[str, str]:
        return {
            "action_type": self.action_type.value,
            "payload_ref": self.payload_ref,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyDecisionControllerAction":
        if not isinstance(payload, dict):
            raise TypeError("study decision controller action payload must be a mapping")
        _reject_unknown_fields("study decision controller action", payload, _CONTROLLER_ACTION_ALLOWED_FIELDS)
        return cls(
            action_type=_payload_text(payload, "action_type", "study decision controller action"),
            payload_ref=_payload_text(payload, "payload_ref", "study decision controller action"),
        )


@dataclass(frozen=True)
class StudyDecisionRecordRef:
    decision_id: str
    artifact_path: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision_id", _require_text("study decision record ref", "decision_id", self.decision_id))
        object.__setattr__(self, "artifact_path", _require_text("study decision record ref", "artifact_path", self.artifact_path))

    def to_dict(self) -> dict[str, str]:
        return {
            "decision_id": self.decision_id,
            "artifact_path": self.artifact_path,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyDecisionRecordRef":
        if not isinstance(payload, dict):
            raise TypeError("study decision record ref payload must be a mapping")
        _reject_unknown_fields("study decision record ref", payload, _RECORD_REF_ALLOWED_FIELDS)
        return cls(
            decision_id=_payload_text(payload, "decision_id", "study decision record ref"),
            artifact_path=_payload_text(payload, "artifact_path", "study decision record ref"),
        )


@dataclass(frozen=True)
class StudyDecisionRecord:
    schema_version: int
    decision_id: str
    study_id: str
    quest_id: str
    emitted_at: str
    decision_type: StudyDecisionType | str
    charter_ref: StudyDecisionCharterRef
    runtime_escalation_ref: RuntimeEscalationRecordRef
    publication_eval_ref: StudyDecisionPublicationEvalRef
    requires_human_confirmation: bool
    controller_actions: tuple[StudyDecisionControllerAction, ...]
    reason: str
    route_target: str | None = None
    route_key_question: str | None = None
    route_rationale: str | None = None
    family_event_envelope: dict[str, Any] | None = None
    family_checkpoint_lineage: dict[str, Any] | None = None
    family_human_gates: tuple[dict[str, Any], ...] = ()
    artifact_path: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.schema_version, int) or isinstance(self.schema_version, bool):
            raise TypeError("study decision record schema_version must be int")
        object.__setattr__(self, "decision_id", _require_text("study decision record", "decision_id", self.decision_id))
        object.__setattr__(self, "study_id", _require_text("study decision record", "study_id", self.study_id))
        object.__setattr__(self, "quest_id", _require_text("study decision record", "quest_id", self.quest_id))
        object.__setattr__(self, "emitted_at", _require_text("study decision record", "emitted_at", self.emitted_at))
        object.__setattr__(self, "decision_type", _normalize_decision_type(self.decision_type))
        object.__setattr__(
            self,
            "charter_ref",
            self.charter_ref
            if isinstance(self.charter_ref, StudyDecisionCharterRef)
            else StudyDecisionCharterRef.from_payload(self.charter_ref),
        )
        object.__setattr__(
            self,
            "runtime_escalation_ref",
            self.runtime_escalation_ref
            if isinstance(self.runtime_escalation_ref, RuntimeEscalationRecordRef)
            else RuntimeEscalationRecordRef.from_payload(self.runtime_escalation_ref),
        )
        object.__setattr__(
            self,
            "publication_eval_ref",
            self.publication_eval_ref
            if isinstance(self.publication_eval_ref, StudyDecisionPublicationEvalRef)
            else StudyDecisionPublicationEvalRef.from_payload(self.publication_eval_ref),
        )
        if not isinstance(self.requires_human_confirmation, bool):
            raise TypeError("study decision record requires_human_confirmation must be bool")
        normalized_actions = tuple(
            action if isinstance(action, StudyDecisionControllerAction) else StudyDecisionControllerAction.from_payload(action)
            for action in self.controller_actions
        )
        if not normalized_actions:
            raise ValueError("study decision record controller_actions must not be empty")
        object.__setattr__(self, "controller_actions", normalized_actions)
        object.__setattr__(self, "reason", _require_text("study decision record", "reason", self.reason))
        normalized_route_target = (
            _require_text("study decision record", "route_target", self.route_target)
            if self.route_target is not None
            else None
        )
        normalized_route_key_question = (
            _require_text("study decision record", "route_key_question", self.route_key_question)
            if self.route_key_question is not None
            else None
        )
        normalized_route_rationale = (
            _require_text("study decision record", "route_rationale", self.route_rationale)
            if self.route_rationale is not None
            else None
        )
        route_contract = (
            normalized_route_target,
            normalized_route_key_question,
            normalized_route_rationale,
        )
        if any(item is not None for item in route_contract) and not all(item is not None for item in route_contract):
            raise ValueError(
                "study decision record route_target, route_key_question, and route_rationale must be provided together"
            )
        object.__setattr__(self, "route_target", normalized_route_target)
        object.__setattr__(self, "route_key_question", normalized_route_key_question)
        object.__setattr__(self, "route_rationale", normalized_route_rationale)
        if self.family_event_envelope is not None and not isinstance(self.family_event_envelope, dict):
            raise TypeError("study decision record family_event_envelope must be mapping or None")
        if self.family_checkpoint_lineage is not None and not isinstance(self.family_checkpoint_lineage, dict):
            raise TypeError("study decision record family_checkpoint_lineage must be mapping or None")
        normalized_family_human_gates = tuple(
            dict(gate) if isinstance(gate, dict) else dict(gate)
            for gate in self.family_human_gates
        )
        for gate in normalized_family_human_gates:
            if not isinstance(gate, dict):
                raise TypeError("study decision record family_human_gates entries must be mappings")
        object.__setattr__(self, "family_human_gates", normalized_family_human_gates)
        if self.artifact_path is not None:
            object.__setattr__(self, "artifact_path", _require_text("study decision record", "artifact_path", self.artifact_path))

    def with_artifact_path(self, artifact_path: str) -> "StudyDecisionRecord":
        return StudyDecisionRecord(
            schema_version=self.schema_version,
            decision_id=self.decision_id,
            study_id=self.study_id,
            quest_id=self.quest_id,
            emitted_at=self.emitted_at,
            decision_type=self.decision_type,
            charter_ref=self.charter_ref,
            runtime_escalation_ref=self.runtime_escalation_ref,
            publication_eval_ref=self.publication_eval_ref,
            requires_human_confirmation=self.requires_human_confirmation,
            controller_actions=self.controller_actions,
            reason=self.reason,
            route_target=self.route_target,
            route_key_question=self.route_key_question,
            route_rationale=self.route_rationale,
            family_event_envelope=dict(self.family_event_envelope) if isinstance(self.family_event_envelope, dict) else None,
            family_checkpoint_lineage=(
                dict(self.family_checkpoint_lineage) if isinstance(self.family_checkpoint_lineage, dict) else None
            ),
            family_human_gates=tuple(dict(gate) for gate in self.family_human_gates),
            artifact_path=artifact_path,
        )

    def ref(self) -> StudyDecisionRecordRef:
        if self.artifact_path is None:
            raise ValueError("study decision record artifact_path must be set before building ref")
        return StudyDecisionRecordRef(
            decision_id=self.decision_id,
            artifact_path=self.artifact_path,
        )

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "schema_version": self.schema_version,
            "decision_id": self.decision_id,
            "study_id": self.study_id,
            "quest_id": self.quest_id,
            "emitted_at": self.emitted_at,
            "decision_type": self.decision_type.value,
            "charter_ref": self.charter_ref.to_dict(),
            "runtime_escalation_ref": self.runtime_escalation_ref.to_dict(),
            "publication_eval_ref": self.publication_eval_ref.to_dict(),
            "requires_human_confirmation": self.requires_human_confirmation,
            "controller_actions": [action.to_dict() for action in self.controller_actions],
            "reason": self.reason,
        }
        if self.route_target is not None:
            payload["route_target"] = self.route_target
            payload["route_key_question"] = self.route_key_question
            payload["route_rationale"] = self.route_rationale
        if self.family_event_envelope is not None:
            payload["family_event_envelope"] = dict(self.family_event_envelope)
        if self.family_checkpoint_lineage is not None:
            payload["family_checkpoint_lineage"] = dict(self.family_checkpoint_lineage)
        if self.family_human_gates or self.family_event_envelope is not None or self.family_checkpoint_lineage is not None:
            payload["family_human_gates"] = [dict(gate) for gate in self.family_human_gates]
        if self.artifact_path is not None:
            payload["artifact_path"] = self.artifact_path
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyDecisionRecord":
        if not isinstance(payload, dict):
            raise TypeError("study decision record payload must be a mapping")
        _reject_unknown_fields("study decision record", payload, _RECORD_ALLOWED_FIELDS)
        return cls(
            schema_version=_payload_int(payload, "schema_version", "study decision record"),
            decision_id=_payload_text(payload, "decision_id", "study decision record"),
            study_id=_payload_text(payload, "study_id", "study decision record"),
            quest_id=_payload_text(payload, "quest_id", "study decision record"),
            emitted_at=_payload_text(payload, "emitted_at", "study decision record"),
            decision_type=_normalize_decision_type(_payload_text(payload, "decision_type", "study decision record")),
            charter_ref=StudyDecisionCharterRef.from_payload(
                _payload_mapping(payload, "charter_ref", "study decision record")
            ),
            runtime_escalation_ref=RuntimeEscalationRecordRef.from_payload(
                _payload_mapping(payload, "runtime_escalation_ref", "study decision record")
            ),
            publication_eval_ref=StudyDecisionPublicationEvalRef.from_payload(
                _payload_mapping(payload, "publication_eval_ref", "study decision record")
            ),
            requires_human_confirmation=_payload_bool(payload, "requires_human_confirmation", "study decision record"),
            controller_actions=tuple(
                StudyDecisionControllerAction.from_payload(action)
                for action in _payload_object_sequence(payload, "controller_actions", "study decision record")
            ),
            reason=_payload_text(payload, "reason", "study decision record"),
            route_target=_optional_payload_text(payload, "route_target"),
            route_key_question=_optional_payload_text(payload, "route_key_question"),
            route_rationale=_optional_payload_text(payload, "route_rationale"),
            family_event_envelope=_optional_payload_mapping(payload, "family_event_envelope", "study decision record"),
            family_checkpoint_lineage=_optional_payload_mapping(
                payload,
                "family_checkpoint_lineage",
                "study decision record",
            ),
            family_human_gates=_optional_payload_mapping_sequence(
                payload,
                "family_human_gates",
                "study decision record",
            ),
            artifact_path=str(payload.get("artifact_path") or "").strip() or None,
        )
