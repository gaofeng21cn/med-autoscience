from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from med_autoscience.paper_mission_transaction import PaperMissionTransaction


CONTRACT_VERSION = "paper-mission-run.v1"
REQUIRED_FIELDS = (
    "mission_id",
    "study_id",
    "objective",
    "mission_state",
    "artifact_delta_ledger",
    "source_refs",
    "paper_audit_pack",
    "authority_touchpoints",
    "forbidden_write_guard",
    "consume_result",
    "claim_permissions",
    "paper_mission_transaction",
)
ALLOWED_MISSION_STATES = frozenset(
    {
        "planned",
        "running",
        "candidate_ready_for_consumption",
        "consumed",
        "route_back",
        "stable_blocker",
        "waiting_human_decision",
        "terminal_handoff",
    }
)
ALLOWED_CONSUME_RESULT_STATUSES = frozenset(
    {
        "not_consumed",
        "accepted",
        "rejected",
        "route_back",
        "typed_blocker",
        "human_gate",
    }
)
FORBIDDEN_AUTHORITY_CLAIMS = frozenset(
    {
        "publication_ready",
        "submission_ready",
        "current_package",
        "owner_receipt_written",
        "typed_blocker_written",
        "human_gate_written",
        "controller_decision_written",
        "publication_eval_written",
        "quality_verdict",
        "artifact_authority",
        "runtime_queue_written",
        "provider_attempt_written",
        "yang_workspace_written",
    }
)
FORBIDDEN_PERMISSION_FLAGS = {
    "can_claim_publication_ready": "publication_ready",
    "can_claim_current_package": "current_package",
    "can_claim_owner_receipt_written": "owner_receipt_written",
}
REQUIRED_GUARD_BLOCKED_PATHS = frozenset(
    {
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
        "current_package",
        "runtime queue/provider attempts",
        "/Users/gaofeng/workspace/Yang/**",
    }
)
REQUIRED_PAPER_AUDIT_PACK_FAMILIES = (
    "analysis_rationale_log",
    "decision_trace",
    "evidence_ledger_delta",
    "review_ledger_delta",
    "revision_log_delta",
    "failed_path_ledger",
    "artifact_lineage",
    "reproducibility_refs",
)
ALLOWED_PAPER_AUDIT_PACK_STATUSES = frozenset(
    {
        "candidate_ref_chain",
        "projection_ref_chain",
        "refs_only_no_write_readback",
        "evidence_gap",
        "typed_blocker_required",
        "not_applicable_with_reason",
    }
)
CANDIDATE_PAPER_AUDIT_PACK_STATUSES = frozenset({"candidate_ref_chain"})
GAP_PAPER_AUDIT_PACK_STATUSES = frozenset(
    {"evidence_gap", "typed_blocker_required", "not_applicable_with_reason"}
)
PLACEHOLDER_AUDIT_REF_KINDS = frozenset(
    {
        "missing_audit_ref",
        "missing_artifact_delta",
        "missing_source_ref",
        "placeholder_ref",
    }
)
PLACEHOLDER_AUDIT_URI_MARKERS = (
    "/missing",
    "/no-artifact-delta-yet",
    "/no-current-diagnostic-ref",
)


class PaperMissionContractError(ValueError):
    """Raised when a PaperMissionRun payload cannot be safely accepted."""


@dataclass(frozen=True)
class PaperMissionRun:
    mission_id: str
    study_id: str
    objective: str
    mission_state: str
    artifact_delta_ledger: tuple[dict[str, Any], ...]
    source_refs: tuple[dict[str, Any], ...]
    paper_audit_pack: dict[str, Any]
    authority_touchpoints: tuple[dict[str, Any], ...]
    forbidden_write_guard: dict[str, Any]
    consume_result: dict[str, Any]
    claim_permissions: dict[str, Any]
    paper_mission_transaction: dict[str, Any]
    payload: dict[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "PaperMissionRun":
        if not isinstance(payload, Mapping):
            raise PaperMissionContractError("PaperMissionRun payload must be a mapping")
        normalized = deepcopy(dict(payload))
        _validate_required_fields(normalized)
        schema_version = _optional_text(normalized.get("schema_version"))
        if schema_version is not None and schema_version != CONTRACT_VERSION:
            raise PaperMissionContractError(
                f"unsupported PaperMissionRun schema_version: {schema_version}"
            )

        mission_id = _required_text(normalized, "mission_id")
        study_id = _required_text(normalized, "study_id")
        objective = _required_text(normalized, "objective")
        mission_state = _required_text(normalized, "mission_state")
        if mission_state not in ALLOWED_MISSION_STATES:
            raise PaperMissionContractError(
                f"unsupported mission_state: {mission_state}"
            )

        artifact_delta_ledger = _required_mapping_list(
            normalized, "artifact_delta_ledger"
        )
        _validate_mapping_items(
            artifact_delta_ledger,
            "artifact_delta_ledger",
            ("delta_id", "artifact_ref", "delta_kind", "status"),
        )
        source_refs = _required_mapping_list(normalized, "source_refs")
        _validate_mapping_items(source_refs, "source_refs", ("ref_id", "ref_kind", "uri"))
        paper_audit_pack = _required_mapping(normalized, "paper_audit_pack")
        _validate_paper_audit_pack(paper_audit_pack)
        authority_touchpoints = _required_mapping_list(
            normalized, "authority_touchpoints"
        )
        _validate_mapping_items(
            authority_touchpoints,
            "authority_touchpoints",
            ("touchpoint_id", "owner", "surface", "status"),
        )

        forbidden_write_guard = _required_mapping(normalized, "forbidden_write_guard")
        _validate_forbidden_write_guard(forbidden_write_guard)
        consume_result = _required_mapping(normalized, "consume_result")
        _validate_consume_result(consume_result)
        claim_permissions = _required_mapping(normalized, "claim_permissions")
        _validate_claim_permissions(claim_permissions)
        paper_mission_transaction = _required_mapping(
            normalized,
            "paper_mission_transaction",
        )
        _validate_paper_mission_transaction(
            paper_mission_transaction=paper_mission_transaction,
            mission_id=mission_id,
            study_id=study_id,
        )

        return cls(
            mission_id=mission_id,
            study_id=study_id,
            objective=objective,
            mission_state=mission_state,
            artifact_delta_ledger=artifact_delta_ledger,
            source_refs=source_refs,
            paper_audit_pack=paper_audit_pack,
            authority_touchpoints=authority_touchpoints,
            forbidden_write_guard=forbidden_write_guard,
            consume_result=consume_result,
            claim_permissions=claim_permissions,
            paper_mission_transaction=paper_mission_transaction,
            payload=normalized,
        ).validate()

    def validate(self) -> "PaperMissionRun":
        _validate_required_fields(self.payload)
        if self.mission_id != _required_text(self.payload, "mission_id"):
            raise PaperMissionContractError("mission_id does not match payload")
        if self.study_id != _required_text(self.payload, "study_id"):
            raise PaperMissionContractError("study_id does not match payload")
        if self.objective != _required_text(self.payload, "objective"):
            raise PaperMissionContractError("objective does not match payload")
        if self.mission_state not in ALLOWED_MISSION_STATES:
            raise PaperMissionContractError(
                f"unsupported mission_state: {self.mission_state}"
            )
        _validate_mapping_items(
            self.artifact_delta_ledger,
            "artifact_delta_ledger",
            ("delta_id", "artifact_ref", "delta_kind", "status"),
        )
        _validate_mapping_items(self.source_refs, "source_refs", ("ref_id", "ref_kind", "uri"))
        _validate_paper_audit_pack(self.paper_audit_pack)
        _validate_mapping_items(
            self.authority_touchpoints,
            "authority_touchpoints",
            ("touchpoint_id", "owner", "surface", "status"),
        )
        _validate_forbidden_write_guard(self.forbidden_write_guard)
        _validate_consume_result(self.consume_result)
        _validate_claim_permissions(self.claim_permissions)
        _validate_paper_mission_transaction(
            paper_mission_transaction=self.paper_mission_transaction,
            mission_id=self.mission_id,
            study_id=self.study_id,
        )
        return self

    def to_dict(self) -> dict[str, Any]:
        return deepcopy(self.payload)


def _validate_required_fields(payload: Mapping[str, Any]) -> None:
    for field in REQUIRED_FIELDS:
        if field not in payload:
            raise PaperMissionContractError(f"missing required field: {field}")


def _required_text(payload: Mapping[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise PaperMissionContractError(f"{field} must be a non-empty string")
    return value.strip()


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise PaperMissionContractError("optional text value must be a non-empty string")
    return value.strip()


def _required_mapping(payload: Mapping[str, Any], field: str) -> dict[str, Any]:
    value = payload.get(field)
    if not isinstance(value, Mapping):
        raise PaperMissionContractError(f"{field} must be a mapping")
    return deepcopy(dict(value))


def _required_mapping_list(
    payload: Mapping[str, Any],
    field: str,
) -> tuple[dict[str, Any], ...]:
    value = payload.get(field)
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise PaperMissionContractError(f"{field} must be a list of mappings")
    items: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise PaperMissionContractError(f"{field}[{index}] must be a mapping")
        items.append(deepcopy(dict(item)))
    return tuple(items)


def _validate_mapping_items(
    items: tuple[dict[str, Any], ...],
    field: str,
    required_fields: tuple[str, ...],
) -> None:
    for index, item in enumerate(items):
        for required_field in required_fields:
            if not _text_from_mapping(item, required_field):
                raise PaperMissionContractError(
                    f"{field}[{index}] missing required field: {required_field}"
                )


def _validate_paper_audit_pack(audit_pack: Mapping[str, Any]) -> None:
    for family in REQUIRED_PAPER_AUDIT_PACK_FAMILIES:
        family_payload = audit_pack.get(family)
        if not isinstance(family_payload, Mapping):
            raise PaperMissionContractError(
                f"paper_audit_pack missing required family: {family}"
            )
        status = _text_from_mapping(family_payload, "status")
        if not status:
            raise PaperMissionContractError(
                f"paper_audit_pack.{family} missing required field: status"
            )
        if status not in ALLOWED_PAPER_AUDIT_PACK_STATUSES:
            raise PaperMissionContractError(
                f"paper_audit_pack.{family} unsupported status: {status}"
            )
        refs = _required_mapping_list(family_payload, "refs")
        if not refs:
            raise PaperMissionContractError(
                f"paper_audit_pack.{family}.refs must not be empty"
            )
        _validate_mapping_items(
            refs,
            f"paper_audit_pack.{family}.refs",
            ("ref_id", "ref_kind", "uri"),
        )
        if status in CANDIDATE_PAPER_AUDIT_PACK_STATUSES:
            _reject_placeholder_audit_refs(family=family, refs=refs)
        if status in GAP_PAPER_AUDIT_PACK_STATUSES:
            _validate_audit_gap_family(family=family, family_payload=family_payload)


def _reject_placeholder_audit_refs(
    *,
    family: str,
    refs: tuple[dict[str, Any], ...],
) -> None:
    for index, ref in enumerate(refs):
        ref_id = _text_from_mapping(ref, "ref_id")
        ref_kind = _text_from_mapping(ref, "ref_kind")
        uri = _text_from_mapping(ref, "uri")
        if (
            ref_kind in PLACEHOLDER_AUDIT_REF_KINDS
            or ref_id.endswith("::missing")
            or any(marker in uri for marker in PLACEHOLDER_AUDIT_URI_MARKERS)
        ):
            raise PaperMissionContractError(
                "paper_audit_pack."
                f"{family}.refs[{index}] candidate status cannot use placeholder ref"
            )


def _validate_audit_gap_family(
    *,
    family: str,
    family_payload: Mapping[str, Any],
) -> None:
    for field in ("gap_class", "gap_reason"):
        if not _text_from_mapping(family_payload, field):
            raise PaperMissionContractError(
                f"paper_audit_pack.{family} gap status missing required field: {field}"
            )


def _validate_forbidden_write_guard(guard: Mapping[str, Any]) -> None:
    candidate_writes_authority = guard.get("candidate_writes_authority")
    if candidate_writes_authority is not False:
        raise PaperMissionContractError(
            "forbidden_write_guard candidate_writes_authority must be false"
        )
    blocked_paths = _string_set(guard.get("blocked_paths"), "blocked_paths")
    missing_blocked_paths = REQUIRED_GUARD_BLOCKED_PATHS - blocked_paths
    if missing_blocked_paths:
        missing = ", ".join(sorted(missing_blocked_paths))
        raise PaperMissionContractError(
            f"forbidden_write_guard missing blocked paths: {missing}"
        )
    forbidden_claims = _string_set(guard.get("forbidden_claims"), "forbidden_claims")
    missing_forbidden_claims = {
        "publication_ready",
        "current_package",
        "owner_receipt_written",
    } - forbidden_claims
    if missing_forbidden_claims:
        missing = ", ".join(sorted(missing_forbidden_claims))
        raise PaperMissionContractError(
            f"forbidden_write_guard missing forbidden claims: {missing}"
        )


def _validate_consume_result(consume_result: Mapping[str, Any]) -> None:
    status = _text_from_mapping(consume_result, "status")
    if status not in ALLOWED_CONSUME_RESULT_STATUSES:
        raise PaperMissionContractError(f"unsupported consume_result status: {status}")


def _validate_claim_permissions(claim_permissions: Mapping[str, Any]) -> None:
    for flag, claim in FORBIDDEN_PERMISSION_FLAGS.items():
        if claim_permissions.get(flag) is not False:
            raise PaperMissionContractError(f"forbidden authority claim: {claim}")
    raw_claims = claim_permissions.get("claims")
    if raw_claims is not None:
        claims = _string_set(raw_claims, "claims")
        forbidden = claims & FORBIDDEN_AUTHORITY_CLAIMS
        if forbidden:
            raise PaperMissionContractError(
                f"forbidden authority claim: {sorted(forbidden)[0]}"
            )


def _validate_paper_mission_transaction(
    *,
    paper_mission_transaction: Mapping[str, Any],
    mission_id: str,
    study_id: str,
) -> None:
    try:
        transaction = PaperMissionTransaction.from_payload(paper_mission_transaction)
    except ValueError as exc:
        raise PaperMissionContractError(
            f"paper_mission_transaction invalid: {exc}"
        ) from exc
    if transaction.mission_id != mission_id:
        raise PaperMissionContractError(
            "paper_mission_transaction mission_id does not match payload"
        )
    if transaction.study_id != study_id:
        raise PaperMissionContractError(
            "paper_mission_transaction study_id does not match payload"
        )


def _text_from_mapping(payload: Mapping[str, Any], field: str) -> str:
    value = payload.get(field)
    return value.strip() if isinstance(value, str) else ""


def _string_set(value: Any, field: str) -> set[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise PaperMissionContractError(f"{field} must be a list of strings")
    result: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise PaperMissionContractError(
                f"{field}[{index}] must be a non-empty string"
            )
        result.add(item.strip())
    return result


__all__ = [
    "ALLOWED_CONSUME_RESULT_STATUSES",
    "ALLOWED_MISSION_STATES",
    "CONTRACT_VERSION",
    "FORBIDDEN_AUTHORITY_CLAIMS",
    "PaperMissionContractError",
    "PaperMissionRun",
]
