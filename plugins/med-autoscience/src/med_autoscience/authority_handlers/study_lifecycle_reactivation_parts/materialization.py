"""Build lifecycle projections and exact CAS operations."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
import base64
from typing import Any

from .._record_validation import (
    RequestShapeError,
    integer,
    mapping,
    sequence,
    text,
    text_list,
)
from .constants import (
    HOST_CAPABILITY_ID,
    _TARGET_ROLE_ORDER,
)
from .primitives import (
    _history_stamp,
    _json_deep_equal,
    _json_fingerprint,
    _raw_bytes_sha256,
    _relative_path,
    _strict_canonical_json_bytes,
    _strict_fingerprint,
    _timestamp,
)
from .request import _projection_target_path


class ProjectionCurrentnessError(ValueError):
    """Raised when a structurally valid projection is stale or incomplete."""


def _absent_relative_path_preconditions(
    request: Mapping[str, Any],
) -> list[str]:
    absent_roles = set(
        request["projection_inventory"]["absent_optional_projection_ids"]
    )
    study_id = request["study_identity"]["study_id"]
    return [
        _projection_target_path(role, study_id)
        for role in _TARGET_ROLE_ORDER
        if role in absent_roles
    ]


def _active_lifecycle_record(request: Mapping[str, Any]) -> dict[str, Any]:
    current = request["current_lifecycle"]["record"]
    wakeup = request["explicit_user_wakeup"]
    intake = request["reviewer_revision_intake"]
    evidence_refs = list(current["evidence_refs"])
    for ref in (intake["intake_ref"], wakeup["user_authority_ref"]):
        if ref not in evidence_refs:
            evidence_refs.append(ref)
    return {
        "schema_version": "mas.study_lifecycle_control.v1",
        "surface_kind": "study_lifecycle_control",
        "study_id": current["study_id"],
        "lifecycle_state": "active",
        "business_status": "active",
        "generation": current["generation"] + 1,
        "recorded_at": wakeup["requested_at"],
        "materialized_at": wakeup["requested_at"],
        "reason_code": wakeup["reason_code"],
        "reason_summary": wakeup["reason_summary"],
        "source_kind": "explicit_user_reviewer_revision_wakeup",
        "source_ref": wakeup["user_authority_ref"],
        "evidence_refs": evidence_refs,
        "lifecycle_ref": "control/lifecycle.json",
        "current_stage_id": None,
        "current_stage_status": None,
        "current_stage_policy": "project_current_runtime_stage",
        "milestone_package_delivered": current["milestone_package_delivered"],
        "submission_ready": False,
        "package_status": current["package_status"],
        "next_action": {
            "surface_kind": "mas_lifecycle_action",
            "action_id": "continue_current_study_line",
            "action_type": "agent_action",
            "owner": "MedAutoScience",
            "status": "active",
            "summary": "Continue the current study line through the canonical MAS route.",
        },
        "resume_policy": {
            "policy_id": "automatic_allowed",
            "auto_resume_allowed": True,
            "explicit_user_wakeup_required": False,
            "allow_stopped_relaunch_required": False,
        },
        "authority_boundary": deepcopy(current["authority_boundary"]),
    }


def _reactivation_receipt(
    request: Mapping[str, Any], after_lifecycle: Mapping[str, Any]
) -> dict[str, Any]:
    current = request["current_lifecycle"]
    wakeup = request["explicit_user_wakeup"]
    intake = request["reviewer_revision_intake"]
    authority_context = request["authority_context"]
    gates = ["explicit_user_wakeup"]
    if current["record"]["lifecycle_state"] == "stopped":
        gates.append("allow_stopped_relaunch")
    core = {
        "receipt_kind": "mas_study_lifecycle_reactivation_receipt",
        "schema_version": 1,
        "owner": "MedAutoScience",
        "study_id": request["study_identity"]["study_id"],
        "handler_call_ref": authority_context["handler_call_ref"],
        "owner_ledger_ref": authority_context["owner_ledger_ref"],
        "original_admission_request_ref": authority_context[
            "original_admission_request_ref"
        ],
        "original_admission_request_sha256": authority_context[
            "original_admission_request_sha256"
        ],
        "admission_scope_id": authority_context["admission_scope_id"],
        "requested_action_id": authority_context["requested_action_id"],
        "requested_run_id": authority_context["requested_run_id"],
        "original_invocation_sha256": authority_context[
            "original_invocation_sha256"
        ],
        "profile_ref": request["profile"]["profile_ref"],
        "profile_sha256": request["profile"]["profile_sha256"],
        "reviewer_revision_intake_ref": intake["intake_ref"],
        "reviewer_revision_intake_sha256": intake["intake_sha256"],
        "user_authority_ref": wakeup["user_authority_ref"],
        "user_authority_sha256": wakeup["user_authority_sha256"],
        "revision_checklist_ref": intake["record"]["revision_checklist_ref"],
        "revision_checklist_sha256": intake["record"]["revision_checklist_sha256"],
        "independent_review_packet_ref": intake["record"][
            "independent_review_packet_ref"
        ],
        "independent_review_packet_sha256": intake["record"][
            "independent_review_packet_sha256"
        ],
        "first_owning_stage_id": intake["record"]["first_owning_stage_id"],
        "allowed_revision_scope": deepcopy(
            intake["record"]["allowed_revision_scope"]
        ),
        "projection_inventory_fingerprint": request["projection_inventory"][
            "inventory_fingerprint"
        ],
        "from_state": current["record"]["lifecycle_state"],
        "from_generation": current["record"]["generation"],
        "from_sha256": current["lifecycle_sha256"],
        "to_state": "active",
        "to_generation": after_lifecycle["generation"],
        "after_sha256": _raw_bytes_sha256(
            _strict_canonical_json_bytes(after_lifecycle)
        ),
        "recorded_at": after_lifecycle["recorded_at"],
        "explicit_user_wakeup": True,
        "allow_stopped_relaunch": wakeup["allow_stopped_relaunch"],
        "satisfied_gate_ids": gates,
        "authorizes_lifecycle_transition": True,
        "authorizes_stage_selection": False,
        "authorizes_publication_or_submission": False,
        "authorizes_attempt_admission_without_materialization": False,
        "requires_opl_cas_materialization_receipt": True,
        "requires_no_in_progress_materialization_journal": True,
        "materialization_semantics": "journaled_all_or_rollback",
        "provider_completion_is_domain_completion": False,
    }
    receipt_fingerprint = _strict_fingerprint(core)
    receipt_ref = (
        "mas-study-lifecycle-reactivation:"
        f"{receipt_fingerprint.removeprefix('sha256:')}"
    )
    return {
        **core,
        "receipt_ref": receipt_ref,
        "receipt_fingerprint": receipt_fingerprint,
    }


def _materialization_operations(
    request: Mapping[str, Any],
    *,
    after_lifecycle: Mapping[str, Any],
    receipt: Mapping[str, Any],
) -> list[dict[str, Any]]:
    targets = {
        item["role"]: item for item in request["projection_inventory"]["targets"]
    }
    current = request["current_lifecycle"]["record"]
    old_state = current["lifecycle_state"]
    study_id = request["study_identity"]["study_id"]
    event_time = after_lifecycle["recorded_at"]
    generation = after_lifecycle["generation"]

    updated_by_role: dict[str, dict[str, Any]] = {
        "study_lifecycle_current": deepcopy(after_lifecycle),
        "workspace_lifecycle_latest": _update_workspace_lifecycle(
            targets["workspace_lifecycle_latest"]["current_payload"],
            current=current,
            after=after_lifecycle,
        ),
        "workspace_index": _update_workspace_index(
            targets["workspace_index"]["current_payload"],
            current=current,
            after=after_lifecycle,
            role="workspace_index",
        ),
    }
    submission_status = _update_submission_status_projection(
        targets["submission_status"]["current_payload"],
        old_state=old_state,
        after=after_lifecycle,
    )
    if submission_status is None:
        if "publication_current_package_status" not in targets:
            raise ProjectionCurrentnessError(
                "foreign submission_status requires "
                "publication_current_package_status lifecycle authority"
            )
    else:
        updated_by_role["submission_status"] = submission_status
    if "workspace_studies_index" in targets:
        updated_by_role["workspace_studies_index"] = _update_workspace_index(
            targets["workspace_studies_index"]["current_payload"],
            current=current,
            after=after_lifecycle,
            role="workspace_studies_index",
        )
    if "workspace_latest_status" in targets:
        updated_by_role["workspace_latest_status"] = _update_workspace_latest_status(
            targets["workspace_latest_status"]["current_payload"],
            updated_workspace_index=updated_by_role["workspace_index"],
            event_time=event_time,
            old_state=old_state,
        )
    if "publication_current_package_status" in targets:
        updated_by_role["publication_current_package_status"] = _update_status_projection(
            targets["publication_current_package_status"]["current_payload"],
            old_state=old_state,
            role="publication_current_package_status",
            after=after_lifecycle,
        )
    if "stage_index" in targets:
        updated_by_role["stage_index"] = _update_stage_index(
            targets["stage_index"]["current_payload"],
            old_state=old_state,
            study_id=study_id,
        )

    operations = []
    for role in _TARGET_ROLE_ORDER:
        target = targets.get(role)
        if target is None or role not in updated_by_role:
            continue
        operations.append(_replace_operation(target, updated_by_role[role]))

    stamp = _history_stamp(event_time)
    history_targets = (
        (
            f"studies/{study_id}/artifacts/controller/lifecycle_control/history/"
            f"{stamp}-g{generation:04d}.json",
            after_lifecycle,
        ),
        (
            f"studies/{study_id}/artifacts/controller/lifecycle_control/history/"
            f"{stamp}-g{generation:04d}-reactivation-receipt.json",
            receipt,
        ),
        (
            "runtime/artifacts/study_lifecycle_control/history/"
            f"{stamp}-{study_id}-g{generation:04d}.json",
            updated_by_role["workspace_lifecycle_latest"],
        ),
    )
    operations.extend(_create_operation(path, payload) for path, payload in history_targets)
    paths = [operation["target_relative_path"] for operation in operations]
    if len(paths) != len(set(paths)):
        raise ProjectionCurrentnessError("materialization target paths are not unique")
    return operations


def _require_projection_fields(
    payload: Mapping[str, Any], role: str, required: set[str]
) -> None:
    missing = sorted(required - set(payload))
    if missing:
        raise ProjectionCurrentnessError(
            f"{role} projection missing required fields: {', '.join(missing)}"
        )


def _update_workspace_lifecycle(
    value: Mapping[str, Any],
    *,
    current: Mapping[str, Any],
    after: Mapping[str, Any],
) -> dict[str, Any]:
    payload = deepcopy(mapping(value, "workspace_lifecycle_latest.current_payload"))
    _require_projection_fields(
        payload,
        "workspace_lifecycle_latest",
        {
            "schema_version",
            "surface_kind",
            "recorded_at",
            "status_counts",
            "changed_study_id",
            "changed_generation",
            "studies",
        },
    )
    if payload.get("schema_version") != "mas.workspace_study_lifecycle_control.v1":
        raise ProjectionCurrentnessError("workspace lifecycle schema is unsupported")
    if payload.get("surface_kind") != "workspace_study_lifecycle_control":
        raise ProjectionCurrentnessError("workspace lifecycle surface is unsupported")
    text(payload["changed_study_id"], "workspace lifecycle changed_study_id")
    changed_generation = integer(
        payload["changed_generation"], "workspace lifecycle changed_generation"
    )
    if changed_generation < 1:
        raise ProjectionCurrentnessError(
            "workspace lifecycle changed_generation must be positive"
        )
    _timestamp(payload["recorded_at"], "workspace lifecycle recorded_at")
    studies = sequence(payload.get("studies"), "workspace lifecycle studies")
    matches = [
        index
        for index, item in enumerate(studies)
        if isinstance(item, Mapping) and item.get("study_id") == current["study_id"]
    ]
    if len(matches) != 1:
        raise ProjectionCurrentnessError(
            "workspace lifecycle must contain exactly one current study record"
        )
    if dict(studies[matches[0]]) != dict(current):
        raise ProjectionCurrentnessError(
            "workspace lifecycle study record does not match exact current lifecycle"
        )
    studies[matches[0]] = deepcopy(after)
    payload["studies"] = studies
    payload["status_counts"] = _updated_status_counts(
        payload.get("status_counts"), current["lifecycle_state"]
    )
    return payload


def _update_workspace_index(
    value: Mapping[str, Any],
    *,
    current: Mapping[str, Any],
    after: Mapping[str, Any],
    role: str,
) -> dict[str, Any]:
    payload = deepcopy(mapping(value, f"{role}.current_payload"))
    _require_projection_fields(
        payload,
        role,
        {"surface_kind", "recorded_at", "status_counts", "studies"},
    )
    if not _supported_workspace_index_envelope(payload):
        raise ProjectionCurrentnessError(
            f"{role} workspace index envelope is unsupported"
        )
    _timestamp(payload["recorded_at"], f"{role} recorded_at")
    studies = sequence(payload.get("studies"), "workspace index studies")
    matches = [
        index
        for index, item in enumerate(studies)
        if isinstance(item, Mapping) and item.get("study_id") == current["study_id"]
    ]
    if len(matches) != 1:
        raise ProjectionCurrentnessError(
            "workspace index must contain exactly one current study entry"
        )
    study = dict(studies[matches[0]])
    _require_projection_fields(
        study,
        f"{role} current study entry",
        {
            "study_id",
            "status",
            "business_status",
            "lifecycle_state",
            "package_status",
        },
    )
    for field in ("status", "business_status", "lifecycle_state"):
        if study.get(field) != current["lifecycle_state"]:
            raise ProjectionCurrentnessError(
                f"workspace index {field} does not match current lifecycle"
            )
    if not _json_deep_equal(study["package_status"], current["package_status"]):
        raise ProjectionCurrentnessError(
            "workspace index package_status does not match current lifecycle"
        )
    if "submission_ready" in study:
        if not _json_deep_equal(
            study["submission_ready"], current["submission_ready"]
        ):
            raise ProjectionCurrentnessError(
                "workspace index submission_ready does not match current lifecycle"
            )
    elif current["submission_ready"] is False:
        study["submission_ready"] = False
    else:
        raise ProjectionCurrentnessError(
            "workspace index cannot infer submission_ready from current lifecycle"
        )
    study.update(
        {
            "status": "active",
            "business_status": "active",
            "lifecycle_state": "active",
            "auto_resume_allowed": True,
            "lifecycle_reason_code": after["reason_code"],
            "lifecycle_reason_summary": after["reason_summary"],
            "next_action": deepcopy(after["next_action"]),
            "resume_policy": deepcopy(after["resume_policy"]),
        }
    )
    studies[matches[0]] = study
    payload["studies"] = studies
    payload["status_counts"] = _updated_status_counts(
        payload.get("status_counts"), current["lifecycle_state"]
    )
    payload["recorded_at"] = after["recorded_at"]
    return payload


def _supported_workspace_index_envelope(payload: Mapping[str, Any]) -> bool:
    return (
        payload.get("surface_kind") == "workspace_index"
        and payload.get("schema_version") == "mas.workspace_index.v1"
        and "version" not in payload
    ) or (
        payload.get("surface_kind") == "opl_workspace_index"
        and payload.get("version") == "workspace-index.v1"
        and "schema_version" not in payload
    )


def _update_workspace_latest_status(
    value: Mapping[str, Any],
    *,
    updated_workspace_index: Mapping[str, Any],
    event_time: str,
    old_state: str,
) -> dict[str, Any]:
    payload = deepcopy(mapping(value, "workspace_latest_status.current_payload"))
    _require_projection_fields(
        payload,
        "workspace_latest_status",
        {
            "surface_kind",
            "schema_version",
            "status_counts",
            "next_required_actions",
            "recorded_at",
        },
    )
    if payload.get("surface_kind") != "workspace_latest_status":
        raise ProjectionCurrentnessError("workspace latest status surface is unsupported")
    schema_version = payload.get("schema_version")
    if not (
        (type(schema_version) is int and schema_version == 1)
        or schema_version == "mas.workspace_status.v1"
    ):
        raise ProjectionCurrentnessError(
            "workspace latest status schema_version is unsupported"
        )
    _timestamp(payload["recorded_at"], "workspace latest status recorded_at")
    text_list(
        payload["next_required_actions"],
        "workspace latest status next_required_actions",
    )
    expected_counts = _updated_status_counts(payload["status_counts"], old_state)
    if expected_counts != updated_workspace_index["status_counts"]:
        raise ProjectionCurrentnessError(
            "workspace latest status counts do not match workspace index currentness"
        )
    payload["status_counts"] = deepcopy(updated_workspace_index["status_counts"])
    payload["next_required_actions"] = list(
        dict.fromkeys(
            item["next_action"]["action_id"]
            for item in updated_workspace_index["studies"]
            if isinstance(item, Mapping)
            and isinstance(item.get("next_action"), Mapping)
            and isinstance(item["next_action"].get("action_id"), str)
        )
    )
    payload["recorded_at"] = event_time
    return payload


def _update_status_projection(
    value: Mapping[str, Any], *, old_state: str, role: str, after: Mapping[str, Any]
) -> dict[str, Any]:
    payload = deepcopy(mapping(value, f"{role}.current_payload"))
    required = {
        "surface_kind",
        "schema_version",
        "lifecycle_state",
        "status",
        "submission_ready",
        "promotion_allowed",
        "recorded_at",
    }
    if role == "submission_status":
        required.add("publication_verdict")
    _require_projection_fields(payload, role, required)
    if payload.get("surface_kind") != "study_current_package_status":
        raise ProjectionCurrentnessError(f"{role} surface is unsupported")
    if type(payload.get("schema_version")) is not int or payload["schema_version"] != 1:
        raise ProjectionCurrentnessError(f"{role} schema_version must be integer 1")
    if payload.get("lifecycle_state") != old_state:
        raise ProjectionCurrentnessError(
            f"{role} lifecycle_state does not match current lifecycle"
        )
    if payload.get("submission_ready") is not False:
        raise ProjectionCurrentnessError(f"{role} unexpectedly claims submission ready")
    if payload.get("promotion_allowed") is not False:
        raise ProjectionCurrentnessError(f"{role} unexpectedly permits promotion")
    if payload.get("status") != "not_ready":
        raise ProjectionCurrentnessError(f"{role} status must remain not_ready")
    if role == "submission_status" and payload.get("publication_verdict") != "not_ready":
        raise ProjectionCurrentnessError(
            "submission_status publication_verdict must remain not_ready"
        )
    if "reason" not in payload and "reason_code" not in payload:
        raise ProjectionCurrentnessError(
            f"{role} must carry a current reason or reason_code"
        )
    _timestamp(payload["recorded_at"], f"{role} recorded_at")
    payload["lifecycle_state"] = "active"
    if "reason" in payload:
        payload["reason"] = after["reason_code"]
    if "reason_code" in payload:
        payload["reason_code"] = after["reason_code"]
    if "reason_summary" in payload:
        payload["reason_summary"] = after["reason_summary"]
    payload["recorded_at"] = after["recorded_at"]
    return payload


def _update_submission_status_projection(
    value: Mapping[str, Any], *, old_state: str, after: Mapping[str, Any]
) -> dict[str, Any] | None:
    payload = deepcopy(mapping(value, "submission_status.current_payload"))
    if "surface_kind" not in payload and isinstance(
        payload.get("schema_version"), str
    ):
        _require_projection_fields(
            payload,
            "foreign submission_status",
            {"schema_version", "authority", "status", "submission_ready"},
        )
        text(payload["schema_version"], "foreign submission_status schema_version")
        if payload.get("authority") is not False:
            raise ProjectionCurrentnessError(
                "foreign submission_status unexpectedly claims authority"
            )
        if payload.get("status") != "not_ready":
            raise ProjectionCurrentnessError(
                "foreign submission_status status must remain not_ready"
            )
        if payload.get("submission_ready") is not False:
            raise ProjectionCurrentnessError(
                "foreign submission_status unexpectedly claims submission ready"
            )
        false_claim_fields = ("promotion_allowed", "mas_owner_receipt_issued")
        for field in false_claim_fields:
            if field in payload and payload[field] is not False:
                raise ProjectionCurrentnessError(
                    f"foreign submission_status unexpectedly claims {field}"
                )
        if (
            "publication_verdict" in payload
            and payload["publication_verdict"] != "not_ready"
        ):
            raise ProjectionCurrentnessError(
                "foreign submission_status unexpectedly claims publication readiness"
            )
        return None
    return _update_status_projection(
        payload,
        old_state=old_state,
        role="submission_status",
        after=after,
    )


def _update_stage_index(
    value: Mapping[str, Any], *, old_state: str, study_id: str
) -> dict[str, Any]:
    payload = deepcopy(mapping(value, "stage_index.current_payload"))
    _require_projection_fields(
        payload,
        "stage_index",
        {"schema_version", "study_id", "lifecycle_state", "stages"},
    )
    schema_version = payload.get("schema_version")
    if type(schema_version) is int and schema_version == 1:
        if payload.get("surface_kind") != "mas_stage_index":
            raise ProjectionCurrentnessError("stage index surface is unsupported")
    elif schema_version == "mas.study_stage_index.v1":
        if "surface_kind" in payload and payload["surface_kind"] != "mas_stage_index":
            raise ProjectionCurrentnessError("stage index surface is unsupported")
    else:
        raise ProjectionCurrentnessError("stage index schema_version is unsupported")
    if payload.get("study_id") != study_id:
        raise ProjectionCurrentnessError("stage index study_id does not match")
    if payload.get("lifecycle_state") != old_state:
        raise ProjectionCurrentnessError(
            "stage index lifecycle_state does not match current lifecycle"
        )
    sequence(payload["stages"], "stage index stages")
    payload["lifecycle_state"] = "active"
    return payload


def _updated_status_counts(value: Any, old_state: str) -> dict[str, int]:
    counts = mapping(value, "status_counts")
    normalized: dict[str, int] = {}
    for key, count in counts.items():
        state = text(key, "status_counts key")
        normalized[state] = integer(count, f"status_counts.{state}")
    if normalized.get(old_state, 0) < 1:
        raise ProjectionCurrentnessError(
            f"status_counts does not contain the current {old_state} study"
        )
    normalized[old_state] -= 1
    if normalized[old_state] == 0:
        normalized.pop(old_state)
    normalized["active"] = normalized.get("active", 0) + 1
    return normalized


def _replace_operation(
    target: Mapping[str, Any], after_json: Mapping[str, Any]
) -> dict[str, Any]:
    after_bytes = _strict_canonical_json_bytes(after_json)
    return {
        "target_relative_path": target["relative_path"],
        "precondition": {
            "kind": "existing_exact",
            "sha256": target["current_sha256"],
            "byte_size": target["current_byte_size"],
        },
        "replacement_bytes_base64": base64.b64encode(after_bytes).decode("ascii"),
        "replacement_sha256": _raw_bytes_sha256(after_bytes),
        "replacement_byte_size": len(after_bytes),
    }


def _create_operation(path: str, after_json: Mapping[str, Any]) -> dict[str, Any]:
    normalized_path = _relative_path(path, "history target path")
    after_bytes = _strict_canonical_json_bytes(after_json)
    return {
        "target_relative_path": normalized_path,
        "precondition": {"kind": "absent"},
        "replacement_bytes_base64": base64.b64encode(after_bytes).decode("ascii"),
        "replacement_sha256": _raw_bytes_sha256(after_bytes),
        "replacement_byte_size": len(after_bytes),
    }


def _cas_authorization(
    *,
    request_id: str,
    operations_sha256: str,
    materialization_scope_sha256: str,
    absent_relative_path_preconditions: list[str],
    authority_receipt_ref: str,
    satisfied_gate_ids: list[str],
) -> dict[str, Any]:
    core = {
        "surface_kind": "mas_lifecycle_cas_mutation_authorization",
        "version": "mas-lifecycle-cas-mutation-authorization.v1",
        "capability_id": HOST_CAPABILITY_ID,
        "request_id": request_id,
        "domain_id": "medautoscience",
        "operations_sha256": operations_sha256,
        "materialization_scope_sha256": materialization_scope_sha256,
        "absent_relative_path_preconditions": deepcopy(
            absent_relative_path_preconditions
        ),
        "authorized": True,
        "authority_receipt_ref": authority_receipt_ref,
        "satisfied_gate_ids": list(satisfied_gate_ids),
    }
    authorization_fingerprint = _strict_fingerprint(core)
    return {
        **core,
        "authorization_ref": (
            "mas-lifecycle-cas-authorization:"
            f"{authorization_fingerprint.removeprefix('sha256:')}"
        ),
        "authorization_fingerprint": authorization_fingerprint,
    }
