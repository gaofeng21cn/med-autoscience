"""Public compatibility surface for study lifecycle reactivation authority."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._record_validation import RequestShapeError
from .study_lifecycle_reactivation_parts.constants import (
    HOST_CAPABILITY_ID,
    REQUEST_KIND,
    RESULT_KIND,
    SCHEMA_VERSION,
    _AUTHORITY_BOUNDARY,
    _INACTIVE_STATES,
    _LIFECYCLE_STATES,
    _OPTIONAL_TARGET_ROLES,
    _PUBLIC_STAGE_ACTION_IDS,
    _REQUIRED_TARGET_ROLES,
    _SAFE_SEGMENT,
    _TARGET_ROLE_ORDER,
)
from .study_lifecycle_reactivation_parts.materialization import (
    ProjectionCurrentnessError,
    _absent_relative_path_preconditions,
    _active_lifecycle_record,
    _cas_authorization,
    _materialization_operations,
    _reactivation_receipt,
)
from .study_lifecycle_reactivation_parts.primitives import _json_fingerprint
from .study_lifecycle_reactivation_parts.request import _normalize_request
from .study_lifecycle_reactivation_parts.result import (
    _finalize,
    _invalid_host_input,
    _typed_blocker,
)


def evaluate_study_lifecycle_reactivation_authority(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a deterministic MAS receipt and an OPL-hosted CAS request."""

    try:
        normalized = _normalize_request(request)
    except RequestShapeError as error:
        return _invalid_host_input(str(error))

    lifecycle = normalized["current_lifecycle"]["record"]
    state = lifecycle["lifecycle_state"]
    if state not in _INACTIVE_STATES:
        return _typed_blocker(
            normalized,
            reason_code="study_lifecycle_is_not_inactive",
            resume_condition=(
                "read the current lifecycle and do not request inactive-study "
                "reactivation for an active study"
            ),
        )
    if not normalized["explicit_user_wakeup"]["explicit_user_wakeup"]:
        return _typed_blocker(
            normalized,
            reason_code="explicit_user_wakeup_required",
            resume_condition="provide a current structured explicit user wakeup",
        )
    if state == "stopped" and not normalized["explicit_user_wakeup"][
        "allow_stopped_relaunch"
    ]:
        return _typed_blocker(
            normalized,
            reason_code="stopped_study_relaunch_authority_required",
            resume_condition=(
                "provide allow_stopped_relaunch=true bound to the same user authority"
            ),
        )
    if normalized["reviewer_revision_intake"]["record"]["status"] not in {
        "accepted",
        "active",
    }:
        return _typed_blocker(
            normalized,
            reason_code="reviewer_revision_intake_not_current",
            resume_condition="provide a current accepted or active reviewer_revision intake",
        )

    after_lifecycle = _active_lifecycle_record(normalized)
    receipt = _reactivation_receipt(normalized, after_lifecycle)
    try:
        operations = _materialization_operations(
            normalized,
            after_lifecycle=after_lifecycle,
            receipt=receipt,
        )
    except (ProjectionCurrentnessError, RequestShapeError) as error:
        return _typed_blocker(
            normalized,
            reason_code="lifecycle_projection_currentness_mismatch",
            resume_condition=str(error),
        )

    absent_relative_path_preconditions = _absent_relative_path_preconditions(
        normalized
    )
    operations_sha256 = _json_fingerprint(operations)
    materialization_scope_sha256 = _json_fingerprint(
        {
            "operations": operations,
            "absent_relative_path_preconditions": (
                absent_relative_path_preconditions
            ),
        }
    )
    request_id = (
        "mas-lifecycle-cas-request:"
        f"{materialization_scope_sha256.removeprefix('sha256:')}"
    )
    authorization = _cas_authorization(
        request_id=request_id,
        operations_sha256=operations_sha256,
        materialization_scope_sha256=materialization_scope_sha256,
        absent_relative_path_preconditions=absent_relative_path_preconditions,
        authority_receipt_ref=receipt["receipt_ref"],
        satisfied_gate_ids=receipt["satisfied_gate_ids"],
    )
    host_request = {
        "surface_kind": "opl_domain_artifact_cas_materialization_request",
        "version": "opl-domain-artifact-cas-materialization.v1",
        "capability_id": HOST_CAPABILITY_ID,
        "request_id": request_id,
        "domain_id": "medautoscience",
        "authorization_ref": authorization["authorization_ref"],
        "operations_sha256": operations_sha256,
        "materialization_scope_sha256": materialization_scope_sha256,
        "absent_relative_path_preconditions": (
            absent_relative_path_preconditions
        ),
        "operations": operations,
    }
    return _finalize(
        normalized,
        status="authorized",
        reactivation_receipt=receipt,
        cas_authorization=authorization,
        host_request=host_request,
    )


__all__ = ["evaluate_study_lifecycle_reactivation_authority"]
