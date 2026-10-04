from __future__ import annotations

import base64
import json
from copy import deepcopy
from typing import Any

import pytest
from jsonschema import ValidationError

from med_autoscience.authority_handlers.study_lifecycle_reactivation import (
    _OPTIONAL_TARGET_ROLES,
    _TARGET_ROLE_ORDER,
    evaluate_study_lifecycle_reactivation_authority,
)
from tests.study_lifecycle_reactivation_authority_cases.fixtures import (
    ROOT,
    STUDY_ID,
    _digest,
    _json_bytes,
    _json_fingerprint,
    _operation_payload,
    _projection_target,
    _rebind_current_lifecycle,
    _rebind_projection_target,
    _rebind_revision_intake,
    _rebind_user_authority,
    _replace_bound_json_bytes,
    _request,
    _request_with_all_optional_projections,
    _request_with_current_multistudy_projection_shape,
    _stage_action_input,
    _validator,
)


def test_paused_reactivation_returns_deterministic_atomic_cas_authority() -> None:
    request = _request()
    assert set(
        request["projection_inventory"]["absent_optional_projection_ids"]
    ) == _OPTIONAL_TARGET_ROLES
    input_validator = _validator(
        "mas-study-lifecycle-reactivation-authority.input.schema.json"
    )
    output_validator = _validator(
        "mas-study-lifecycle-reactivation-authority.output.schema.json"
    )
    input_validator.validate(request)

    result = evaluate_study_lifecycle_reactivation_authority(request)
    assert result == evaluate_study_lifecycle_reactivation_authority(request)
    output_validator.validate(result)
    assert result["status"] == "authorized"

    receipt = result["reactivation_receipt"]
    assert receipt["from_state"] == "paused"
    assert receipt["from_generation"] == 1
    assert receipt["to_state"] == "active"
    assert receipt["to_generation"] == 2
    assert receipt["satisfied_gate_ids"] == ["explicit_user_wakeup"]
    assert receipt["authorizes_stage_selection"] is False
    assert receipt["authorizes_attempt_admission_without_materialization"] is False
    assert receipt["requested_action_id"] == "baseline_and_evidence_setup"
    assert receipt["requested_run_id"] == "stage-run-001"
    assert receipt["materialization_semantics"] == "journaled_all_or_rollback"

    host_request = result["opl_host_materialization_request"]
    authorization = result["mas_lifecycle_cas_mutation_authorization"]
    assert host_request["capability_id"] == "opl_domain_artifact_cas_materialization.v1"
    assert authorization["operations_sha256"] == host_request["operations_sha256"]
    assert host_request["version"] == "opl-domain-artifact-cas-materialization.v1"
    assert host_request["authorization_ref"] == authorization["authorization_ref"]
    assert authorization["authority_receipt_ref"] == receipt["receipt_ref"]
    operations = host_request["operations"]
    absent_paths = [
        "reports/studies_index.json",
        "reports/latest_status.json",
        f"studies/{STUDY_ID}/publication/current_package/STATUS.json",
        f"studies/{STUDY_ID}/control/stage_index.json",
    ]
    expected_scope_sha256 = _json_fingerprint(
        {
            "operations": operations,
            "absent_relative_path_preconditions": absent_paths,
        }
    )
    assert host_request["absent_relative_path_preconditions"] == absent_paths
    assert authorization["absent_relative_path_preconditions"] == absent_paths
    assert host_request["materialization_scope_sha256"] == expected_scope_sha256
    assert authorization["materialization_scope_sha256"] == expected_scope_sha256
    assert host_request["request_id"] == (
        "mas-lifecycle-cas-request:"
        f"{expected_scope_sha256.removeprefix('sha256:')}"
    )
    assert len(operations) == 7
    paths = {operation["target_relative_path"] for operation in operations}
    assert f"studies/{STUDY_ID}/control/lifecycle.json" in paths
    assert f"studies/{STUDY_ID}/submission/STATUS.json" in paths
    assert any("lifecycle_control/history/" in path for path in paths)
    receipt_operations = [
        operation
        for operation in operations
        if operation["target_relative_path"].endswith(
            "-reactivation-receipt.json"
        )
    ]
    assert len(receipt_operations) == 1
    assert "/artifacts/controller/lifecycle_control/history/" in receipt_operations[
        0
    ]["target_relative_path"]
    receipt_bytes = base64.b64decode(
        receipt_operations[0]["replacement_bytes_base64"]
    )
    assert receipt_bytes == _json_bytes(receipt)
    assert json.loads(receipt_bytes) == receipt
    create_operations = [
        operation for operation in operations if operation["precondition"]["kind"] == "absent"
    ]
    assert len(create_operations) == 3
    assert all("requested" not in operation for operation in create_operations)

    submission_operation = next(
        operation
        for operation in operations
        if operation["target_relative_path"].endswith("submission/STATUS.json")
    )
    submission = json.loads(
        base64.b64decode(submission_operation["replacement_bytes_base64"])
    )
    assert submission["lifecycle_state"] == "active"
    assert submission["status"] == "not_ready"
    assert submission["submission_ready"] is False
    assert submission["publication_verdict"] == "not_ready"
    assert submission["reason"] == "reviewer_revision_reactivation"
    assert submission["recorded_at"] == "2026-07-21T01:00:00Z"


def test_reactivation_preserves_an_opl_workspace_index_envelope() -> None:
    request = _request()
    target = _projection_target(request, "workspace_index")
    target["record"].pop("schema_version")
    target["record"]["surface_kind"] = "opl_workspace_index"
    target["record"]["version"] = "workspace-index.v1"
    _rebind_projection_target(target)

    result = evaluate_study_lifecycle_reactivation_authority(request)
    operation = next(
        item
        for item in result["opl_host_materialization_request"]["operations"]
        if item["target_relative_path"] == "workspace_index.json"
    )
    updated = _operation_payload(operation)

    assert updated["surface_kind"] == "opl_workspace_index"
    assert updated["version"] == "workspace-index.v1"
    assert "schema_version" not in updated
    assert updated["studies"][0]["lifecycle_state"] == "active"


def test_requested_run_id_is_bound_through_receipt_and_authorization() -> None:
    first = evaluate_study_lifecycle_reactivation_authority(_request())
    second_request = _request()
    second_request["authority_context"]["requested_run_id"] = "stage-run-002"
    second = evaluate_study_lifecycle_reactivation_authority(second_request)

    assert first["status"] == second["status"] == "authorized"
    assert first["reactivation_receipt"]["receipt_ref"] != second[
        "reactivation_receipt"
    ]["receipt_ref"]
    assert first["mas_lifecycle_cas_mutation_authorization"][
        "authorization_ref"
    ] != second["mas_lifecycle_cas_mutation_authorization"]["authorization_ref"]
    assert first["opl_host_materialization_request"][
        "materialization_scope_sha256"
    ] != second["opl_host_materialization_request"][
        "materialization_scope_sha256"
    ]


def test_all_projection_sources_share_handler_order_and_are_authorized() -> None:
    expected_order = list(_TARGET_ROLE_ORDER)
    catalog = json.loads(
        (ROOT / "contracts/action_catalog.json").read_text(encoding="utf-8")
    )
    lifecycle_contract = json.loads(
        (ROOT / "contracts/study_lifecycle_reactivation_contract.json").read_text(
            encoding="utf-8"
        )
    )
    assert [
        item["projection_id"] for item in lifecycle_contract["projection_sources"]
    ] == expected_order
    for stage_action in catalog["actions"][:6]:
        sources = stage_action["authority_boundary"][
            "lifecycle_admission_contract"
        ]["reactivation_projection_sources"]
        assert [item["projection_id"] for item in sources] == expected_order

    request = _request_with_all_optional_projections()
    _validator(
        "mas-study-lifecycle-reactivation-authority.input.schema.json"
    ).validate(request)
    result = evaluate_study_lifecycle_reactivation_authority(request)
    _validator(
        "mas-study-lifecycle-reactivation-authority.output.schema.json"
    ).validate(result)

    assert result["status"] == "authorized"
    host_request = result["opl_host_materialization_request"]
    authorization = result["mas_lifecycle_cas_mutation_authorization"]
    assert [
        target["projection_id"]
        for target in request["projection_inventory"]["targets"]
    ] == expected_order
    assert host_request["absent_relative_path_preconditions"] == []
    assert authorization["absent_relative_path_preconditions"] == []
    operations = host_request["operations"]
    assert len(operations) == 11
    assert [item["target_relative_path"] for item in operations[:8]] == [
        f"studies/{STUDY_ID}/control/lifecycle.json",
        "runtime/artifacts/study_lifecycle_control/latest.json",
        "workspace_index.json",
        "reports/studies_index.json",
        "reports/latest_status.json",
        f"studies/{STUDY_ID}/submission/STATUS.json",
        f"studies/{STUDY_ID}/publication/current_package/STATUS.json",
        f"studies/{STUDY_ID}/control/stage_index.json",
    ]


def test_current_multistudy_legacy_projection_roundtrip_is_narrow_and_cas_bound() -> None:
    request = _request_with_current_multistudy_projection_shape()
    request_before = deepcopy(request)
    other_study_id = "004-dpcc-longitudinal-care-inertia-intensification-gap"
    shared_roles = (
        "workspace_lifecycle_latest",
        "workspace_index",
        "workspace_studies_index",
    )
    other_study_fingerprints = {
        role: _json_fingerprint(
            next(
                study
                for study in _projection_target(request, role)["record"]["studies"]
                if study["study_id"] == other_study_id
            )
        )
        for role in shared_roles
    }
    last_changed = {
        field: _projection_target(request, "workspace_lifecycle_latest")["record"][
            field
        ]
        for field in ("changed_study_id", "changed_generation", "recorded_at")
    }

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert request == request_before
    assert result["status"] == "authorized"
    operations = result["opl_host_materialization_request"]["operations"]
    assert len(operations) == 10
    operation_by_path = {
        operation["target_relative_path"]: operation for operation in operations
    }
    assert f"studies/{STUDY_ID}/submission/STATUS.json" not in operation_by_path

    role_paths = {
        role: _projection_target(request, role)["relative_path"]
        if _projection_target(request, role)["root"] == "workspace"
        else f"studies/{STUDY_ID}/{_projection_target(request, role)['relative_path']}"
        for role in shared_roles
    }
    for role, target_path in role_paths.items():
        operation = operation_by_path[target_path]
        assert operation["precondition"]["kind"] == "existing_exact"
        assert operation["precondition"]["sha256"] == _projection_target(
            request, role
        )["sha256"].removeprefix("sha256:")
        updated = _operation_payload(operation)
        other_study = next(
            study
            for study in updated["studies"]
            if study["study_id"] == other_study_id
        )
        assert _json_fingerprint(other_study) == other_study_fingerprints[role]

    updated_workspace_lifecycle = _operation_payload(
        operation_by_path[role_paths["workspace_lifecycle_latest"]]
    )
    assert {
        field: updated_workspace_lifecycle[field]
        for field in ("changed_study_id", "changed_generation", "recorded_at")
    } == last_changed

    for role in ("workspace_index", "workspace_studies_index"):
        updated_index = _operation_payload(operation_by_path[role_paths[role]])
        target_study = next(
            study for study in updated_index["studies"] if study["study_id"] == STUDY_ID
        )
        assert target_study["lifecycle_state"] == "active"
        assert target_study["submission_ready"] is False

    latest_status_path = "reports/latest_status.json"
    assert _operation_payload(operation_by_path[latest_status_path])["schema_version"] == (
        "mas.workspace_status.v1"
    )
    stage_index_path = f"studies/{STUDY_ID}/control/stage_index.json"
    updated_stage_index = _operation_payload(operation_by_path[stage_index_path])
    assert updated_stage_index["schema_version"] == "mas.study_stage_index.v1"
    assert "surface_kind" not in updated_stage_index
    assert updated_stage_index["lifecycle_state"] == "active"

    publication_status_path = (
        f"studies/{STUDY_ID}/publication/current_package/STATUS.json"
    )
    assert _operation_payload(operation_by_path[publication_status_path])[
        "lifecycle_state"
    ] == "active"


def test_foreign_submission_status_requires_lifecycle_owned_package_status() -> None:
    request = _request_with_current_multistudy_projection_shape()
    request["projection_inventory"]["targets"] = [
        target
        for target in request["projection_inventory"]["targets"]
        if target["projection_id"] != "publication_current_package_status"
    ]
    request["projection_inventory"]["absent_optional_projection_ids"] = [
        "publication_current_package_status"
    ]

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "typed_blocker"
    assert result["typed_blocker"]["reason_code"] == (
        "lifecycle_projection_currentness_mismatch"
    )
    assert "requires publication_current_package_status" in result["typed_blocker"][
        "resume_condition"
    ]
    assert result["opl_host_materialization_request"] is None


@pytest.mark.parametrize(
    ("field", "claim"),
    [
        ("authority", True),
        ("status", "ready"),
        ("submission_ready", True),
        ("mas_owner_receipt_issued", True),
        ("publication_verdict", "ready"),
    ],
)
def test_foreign_submission_status_readiness_or_authority_claim_fails_closed(
    field: str, claim: Any
) -> None:
    request = _request_with_current_multistudy_projection_shape()
    submission = _projection_target(request, "submission_status")
    submission["record"][field] = claim
    _rebind_projection_target(submission)

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "typed_blocker"
    assert result["typed_blocker"]["reason_code"] == (
        "lifecycle_projection_currentness_mismatch"
    )
    assert result["opl_host_materialization_request"] is None
    assert result["mas_lifecycle_cas_mutation_authorization"] is None


def test_stopped_reactivation_requires_separate_relaunch_authority() -> None:
    request = _request("stopped")
    request["reactivation_request"]["allow_stopped_relaunch"] = False
    request["user_authority"]["record"]["allow_stopped_relaunch"] = False
    _rebind_user_authority(request)

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "typed_blocker"
    assert result["typed_blocker"]["reason_code"] == (
        "stopped_study_relaunch_authority_required"
    )
    assert result["opl_host_materialization_request"] is None


def test_missing_explicit_wakeup_is_a_typed_blocker() -> None:
    request = _request()
    request["reactivation_request"]["explicit_user_wakeup"] = False
    request["user_authority"]["record"]["explicit_user_wakeup"] = False
    _rebind_user_authority(request)

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "typed_blocker"
    assert result["typed_blocker"]["reason_code"] == "explicit_user_wakeup_required"


def test_stale_projection_fails_closed_before_any_cas_request() -> None:
    request = _request()
    submission = next(
        item
        for item in request["projection_inventory"]["targets"]
        if item["projection_id"] == "submission_status"
    )
    submission["record"]["lifecycle_state"] = "active"
    _rebind_projection_target(submission)

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "typed_blocker"
    assert result["typed_blocker"]["reason_code"] == (
        "lifecycle_projection_currentness_mismatch"
    )
    assert result["mas_lifecycle_cas_mutation_authorization"] is None


@pytest.mark.parametrize(
    ("projection_id", "missing_field"),
    [
        ("workspace_lifecycle_latest", "status_counts"),
        ("workspace_index", "studies"),
        ("workspace_studies_index", "studies"),
        ("workspace_latest_status", "status_counts"),
        ("submission_status", "reason"),
        ("publication_current_package_status", "reason"),
        ("stage_index", "stages"),
    ],
)
def test_incomplete_projection_returns_closed_typed_blocker(
    projection_id: str, missing_field: str
) -> None:
    request = _request_with_all_optional_projections()
    projection = next(
        target
        for target in request["projection_inventory"]["targets"]
        if target["projection_id"] == projection_id
    )
    projection["record"].pop(missing_field)
    _rebind_projection_target(projection)

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "typed_blocker"
    assert result["typed_blocker"]["reason_code"] == (
        "lifecycle_projection_currentness_mismatch"
    )
    assert result["opl_host_materialization_request"] is None
    assert result["mas_lifecycle_cas_mutation_authorization"] is None


@pytest.mark.parametrize(
    ("projection_id", "missing_field"),
    [
        ("workspace_index", "package_status"),
        ("workspace_studies_index", "package_status"),
    ],
)
def test_incomplete_workspace_study_entry_returns_closed_typed_blocker(
    projection_id: str, missing_field: str
) -> None:
    request = _request_with_all_optional_projections()
    projection = next(
        target
        for target in request["projection_inventory"]["targets"]
        if target["projection_id"] == projection_id
    )
    projection["record"]["studies"][0].pop(missing_field)
    _rebind_projection_target(projection)

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "typed_blocker"
    assert result["typed_blocker"]["reason_code"] == (
        "lifecycle_projection_currentness_mismatch"
    )
    assert result["opl_host_materialization_request"] is None
    assert result["mas_lifecycle_cas_mutation_authorization"] is None


@pytest.mark.parametrize("projection_id", ["workspace_index", "workspace_studies_index"])
@pytest.mark.parametrize(
    ("field", "stale_value"),
    [("package_status", "ready"), ("submission_ready", 0)],
)
def test_workspace_study_entry_preserved_fields_are_type_strict_and_current(
    projection_id: str, field: str, stale_value: Any
) -> None:
    request = _request_with_all_optional_projections()
    projection = next(
        target
        for target in request["projection_inventory"]["targets"]
        if target["projection_id"] == projection_id
    )
    projection["record"]["studies"][0][field] = stale_value
    _rebind_projection_target(projection)

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "typed_blocker"
    assert result["typed_blocker"]["reason_code"] == (
        "lifecycle_projection_currentness_mismatch"
    )
    assert result["opl_host_materialization_request"] is None
    assert result["mas_lifecycle_cas_mutation_authorization"] is None


def test_projection_finite_number_overflow_is_invalid_before_authorization() -> None:
    request = _request()
    projection = request["projection_inventory"]["targets"][1]
    projection["record"]["overflow_probe"] = float("inf")
    encoded_record = deepcopy(projection["record"])
    encoded_record["overflow_probe"] = "__JSON_NUMBER_OVERFLOW__"
    raw_bytes = _json_bytes(encoded_record).replace(
        b'"__JSON_NUMBER_OVERFLOW__"', b"1e400"
    )
    _replace_bound_json_bytes(
        projection,
        raw_bytes,
        bytes_field="bytes_base64",
        byte_size_field="byte_size",
        sha256_field="sha256",
    )

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "invalid_host_input"
    assert "non-finite JSON number" in result["error"]["detail"]
    assert result["opl_host_materialization_request"] is None
    assert result["mas_lifecycle_cas_mutation_authorization"] is None


def test_mixed_user_authority_is_invalid_host_input() -> None:
    request = _request()
    request["reactivation_request"]["user_authority_ref"] = (
        "file:///workspace/control/different-user-authority.json"
    )

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "invalid_host_input"
    assert "must match" in result["error"]["detail"]


def test_user_authority_flags_must_match_public_wakeup_request() -> None:
    request = _request()
    request["reactivation_request"]["explicit_user_wakeup"] = False

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "invalid_host_input"
    assert "explicit_user_wakeup must match" in result["error"]["detail"]


def test_user_instruction_digest_is_recomputed_by_handler() -> None:
    request = _request()
    request["user_authority"]["record"]["instruction_text"] = "Different instruction."
    _rebind_user_authority(request)

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "invalid_host_input"
    assert "does not match normalized instruction_text" in result["error"]["detail"]


@pytest.mark.parametrize(
    "binding",
    ["user_authority", "reviewer_revision_intake", "current_lifecycle", "projection"],
)
def test_supplied_record_must_deep_equal_exact_json_bytes(binding: str) -> None:
    request = _request()
    if binding == "projection":
        bound_record = request["projection_inventory"]["targets"][0]["record"]
    else:
        bound_record = request[binding]["record"]
    bound_record["request_only"] = True

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "invalid_host_input"
    assert "deep-equal" in result["error"]["detail"]


def test_exact_json_record_deep_equality_is_type_strict() -> None:
    request = _request()
    request["user_authority"]["record"]["owner_receipt"] = 0

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "invalid_host_input"
    assert "deep-equal" in result["error"]["detail"]


@pytest.mark.parametrize(
    ("raw_bytes", "expected_detail"),
    [
        (b"{", "strict JSON object"),
        (b"\xff", "strict UTF-8"),
        (b"[]", "JSON object"),
        (
            b'{"surface_kind":"first","surface_kind":"second"}',
            "duplicate JSON object key",
        ),
        (b'{"value":NaN}', "non-standard JSON constant"),
        (b'{"value":Infinity}', "non-standard JSON constant"),
    ],
)
def test_user_authority_requires_strict_json_object_bytes(
    raw_bytes: bytes, expected_detail: str
) -> None:
    request = _request()
    _replace_bound_json_bytes(
        request["user_authority"],
        raw_bytes,
        bytes_field="authority_bytes_base64",
        byte_size_field="authority_byte_size",
        sha256_field="authority_sha256",
    )

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "invalid_host_input"
    assert expected_detail in result["error"]["detail"]


@pytest.mark.parametrize(
    ("encoded", "expected_detail"),
    [
        ("not+base64%%%", "bytes_base64 is malformed"),
        ("e31=", "bytes_base64 must be canonical base64"),
    ],
)
def test_base64_must_be_well_formed_and_canonical(
    encoded: str, expected_detail: str
) -> None:
    request = _request()
    request["reviewer_revision_intake"]["intake_bytes_base64"] = encoded

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "invalid_host_input"
    assert expected_detail in result["error"]["detail"]


def test_exact_json_byte_size_is_recomputed_by_handler() -> None:
    request = _request()
    request["current_lifecycle"]["lifecycle_byte_size"] += 1

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "invalid_host_input"
    assert "byte_size does not match decoded bytes" in result["error"]["detail"]


def test_projection_sha256_is_recomputed_from_raw_bytes() -> None:
    request = _request()
    request["projection_inventory"]["targets"][0]["sha256"] = _digest(
        "not-the-projection"
    )

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "invalid_host_input"
    assert "sha256 does not match decoded bytes" in result["error"]["detail"]


@pytest.mark.parametrize("binding", ["user_authority", "reviewer_revision_intake"])
def test_wakeup_evidence_recorded_at_must_equal_requested_at(binding: str) -> None:
    request = _request()
    request[binding]["record"]["recorded_at"] = "2026-07-21T00:59:59Z"
    if binding == "user_authority":
        _rebind_user_authority(request)
    else:
        _rebind_revision_intake(request)

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "invalid_host_input"
    assert "recorded_at must match wakeup requested_at" in result["error"]["detail"]


@pytest.mark.parametrize("lifecycle_field", ["recorded_at", "materialized_at"])
def test_requested_at_must_be_strictly_later_than_lifecycle(
    lifecycle_field: str,
) -> None:
    request = _request()
    lifecycle = request["current_lifecycle"]["record"]
    lifecycle[lifecycle_field] = request["reactivation_request"]["requested_at"]
    _rebind_current_lifecycle(request)

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "invalid_host_input"
    assert f"later than current lifecycle {lifecycle_field}" in result["error"][
        "detail"
    ]


def test_old_authority_and_intake_cannot_replay_for_later_generation() -> None:
    request = _request()
    lifecycle = request["current_lifecycle"]["record"]
    lifecycle["generation"] = 3
    lifecycle["recorded_at"] = "2026-07-22T00:00:00Z"
    lifecycle["materialized_at"] = "2026-07-22T00:00:01Z"
    _rebind_current_lifecycle(request)

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "invalid_host_input"
    assert "strictly later" in result["error"]["detail"]


def test_observed_generation_must_match_exact_lifecycle_generation() -> None:
    request = _request()
    request["reactivation_request"]["observed_lifecycle_generation"] = 2

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "invalid_host_input"
    assert "state/generation does not match" in result["error"]["detail"]


def test_requested_stage_must_match_revision_intake_first_owner() -> None:
    request = _request()
    request["authority_context"]["requested_action_id"] = (
        "finalize_and_publication_handoff"
    )

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "invalid_host_input"
    assert "requested_action_id must match" in result["error"]["detail"]


def test_public_request_mode_is_minimal_and_closed() -> None:
    validator = _validator("mas-stage-action.input.schema.json")
    admission = {
        "surface_kind": "opl_domain_lifecycle_admission",
        "version": "opl-domain-lifecycle-admission.v1",
        "mode": "reactivation_request",
        "reactivation_request": {
            "profile_ref": "file:///workspace/profile.json",
            "profile_sha256": _digest("profile"),
            "user_authority_ref": "file:///workspace/user-authority.json",
            "user_authority_sha256": _digest("user-authority"),
            "reviewer_revision_intake_ref": "file:///workspace/revision.json",
            "reviewer_revision_intake_sha256": _digest("revision"),
            "current_lifecycle_ref": "file:///workspace/lifecycle.json",
            "current_lifecycle_sha256": _digest("lifecycle"),
            "observed_lifecycle_state": "paused",
            "observed_lifecycle_generation": 1,
            "explicit_user_wakeup": True,
            "allow_stopped_relaunch": False,
            "requested_at": "2026-07-21T01:00:00Z",
            "reason_code": "reviewer_revision_reactivation",
            "reason_summary": "Reactivate for reviewer revision.",
        },
    }
    validator.validate(_stage_action_input(admission))

    injected = deepcopy(admission)
    injected["reactivation_request"]["handler_call_ref"] = "file:///host/call.json"
    with pytest.raises(ValidationError):
        validator.validate(_stage_action_input(injected))


def test_materialized_receipt_mode_is_closed() -> None:
    validator = _validator("mas-stage-action.input.schema.json")
    admission = {
        "surface_kind": "opl_domain_lifecycle_admission",
        "version": "opl-domain-lifecycle-admission.v1",
        "mode": "materialized_receipt",
        "domain_authority_result_ref": "file:///host/authority-result.json",
        "domain_authority_result_sha256": _digest("authority-result"),
        "materialization_receipt_ref": "file:///host/materialization-receipt.json",
        "materialization_receipt_sha256": _digest("materialization-receipt"),
    }
    validator.validate(_stage_action_input(admission))

    widened = deepcopy(admission)
    widened["launch_clearance"] = True
    with pytest.raises(ValidationError):
        validator.validate(_stage_action_input(widened))


def test_registry_catalog_and_stage_admission_are_internal_and_closed() -> None:
    registry = json.loads(
        (ROOT / "contracts/domain_handler_registry.json").read_text(encoding="utf-8")
    )
    catalog = json.loads(
        (ROOT / "contracts/action_catalog.json").read_text(encoding="utf-8")
    )
    assert len(catalog["actions"]) == 12
    assert [item["action_id"] for item in catalog["actions"]] == [
        "direction_and_route_selection",
        "baseline_and_evidence_setup",
        "bounded_analysis_campaign",
        "manuscript_authoring",
        "review_and_quality_gate",
        "finalize_and_publication_handoff",
        "qualification_work_item_provisioning_authority_evaluate",
        "study_initialization_authority_evaluate",
        "study_lifecycle_reactivation_authority_evaluate",
        "candidate_admission_authority_evaluate",
        "build_dependency_currentness_authority_evaluate",
        "paper_mission_authority_evaluate",
    ]
    lifecycle_contract = json.loads(
        (ROOT / "contracts/study_lifecycle_reactivation_contract.json").read_text(
            encoding="utf-8"
        )
    )
    stage_schema = json.loads(
        (ROOT / "contracts/schemas/v2/mas-stage-action.input.schema.json").read_text(
            encoding="utf-8"
        )
    )
    handler = next(
        item
        for item in registry["handlers"]
        if item["handler_id"] == "mas.study-lifecycle-reactivation-authority-evaluate"
    )
    assert handler["binding"] == {
        "kind": "python_callable",
        "module": "med_autoscience.authority_handlers.study_lifecycle_reactivation",
        "callable": "evaluate_study_lifecycle_reactivation_authority",
    }
    action = next(
        item
        for item in catalog["actions"]
        if item["action_id"] == "study_lifecycle_reactivation_authority_evaluate"
    )
    assert all(value is None for value in action["supported_surfaces"].values())
    assert action["authority_boundary"]["public_action"] is False
    assert action["authority_boundary"][
        "supported_surfaces_null_is_not_runtime_access_control"
    ] is True
    assert action["authority_boundary"][
        "handler_raw_byte_self_validation_required"
    ] is True
    assert action["authority_boundary"]["host_materialization_contract"] == {
        "capability_id": "opl_domain_artifact_cas_materialization.v1",
        "request_output_field": "opl_host_materialization_request",
        "authorization_output_field": "mas_lifecycle_cas_mutation_authorization",
        "materialization_scope_sha256_field": "materialization_scope_sha256",
        "absent_relative_path_preconditions_field": (
            "absent_relative_path_preconditions"
        ),
    }
    assert lifecycle_contract["authority_boundary"]["public_action"] is False
    assert lifecycle_contract["authority_boundary"][
        "supported_surfaces_null_is_not_runtime_access_control"
    ] is True
    build_currentness = next(
        item for item in catalog["actions"]
        if item["action_id"] == "build_dependency_currentness_authority_evaluate"
    )
    assert build_currentness["execution_binding"] == {
        "kind": "handler_ref",
        "handler_ref": "handler:mas.build-dependency-currentness-authority-evaluate",
    }
    assert build_currentness["input_schema_ref"] == (
        "contracts/schemas/v2/"
        "mas-build-dependency-currentness-authority.input.schema.json"
    )
    assert build_currentness["output_schema_ref"] == (
        "contracts/schemas/v2/"
        "mas-build-dependency-currentness-authority.output.schema.json"
    )
    assert all(
        value is None for value in build_currentness["supported_surfaces"].values()
    )
    assert "managed_authority_provenance_dependency" not in build_currentness
    build_boundary = build_currentness["authority_boundary"]
    assert {
        "requires_distinct_managed_authority_attempt": True,
        "requires_managed_authority_attempt_provenance": True,
        "requires_managed_authority_attempt_receipt": True,
        "requires_owner_ledger_ref": True,
        "requires_owner_ledger_provenance": True,
        "opl_must_persist_owner_result_before_paper_mission_injection": True,
        "paper_mission_host_context_authority_ref_field": (
            "build_dependency_currentness_authority_ref"
        ),
        "paper_mission_host_context_issuer_attempt_ref_field": (
            "build_dependency_currentness_authority_issuer_attempt_ref"
        ),
        "runtime_integration_status": "declared_not_current",
        "missing_provenance_effect": "fail_closed",
    }.items() <= build_boundary.items()
    assert build_boundary["independent_trust_root"] is False
    assert build_boundary[
        "malicious_host_complete_self_consistent_forgery_resistance"
    ] is False
    paper_mission = next(
        item for item in catalog["actions"]
        if item["action_id"] == "paper_mission_authority_evaluate"
    )
    assert paper_mission["optional_fields"] == [
        "selected_build_currentness_authority",
        "revision_consumption",
    ]
    assert "build-dependency-currentness" in catalog["notes"][1]
    assert lifecycle_contract["authority_boundary"][
        "handler_raw_byte_self_validation_required"
    ] is True
    assert len(stage_schema["$defs"]["lifecycle_admission"]["oneOf"]) == 2
    exact_byte_binding_fields = {
        "user_authority": {
            "bytes_base64": "authority_bytes_base64",
            "byte_size": "authority_byte_size",
            "sha256": "authority_sha256",
            "record": "record",
        },
        "reviewer_revision_intake": {
            "bytes_base64": "intake_bytes_base64",
            "byte_size": "intake_byte_size",
            "sha256": "intake_sha256",
            "record": "record",
        },
        "current_lifecycle": {
            "bytes_base64": "lifecycle_bytes_base64",
            "byte_size": "lifecycle_byte_size",
            "sha256": "lifecycle_sha256",
            "record": "record",
        },
        "projection_target": {
            "bytes_base64": "bytes_base64",
            "byte_size": "byte_size",
            "sha256": "sha256",
            "record": "record",
        },
    }
    assert lifecycle_contract["exact_byte_binding_fields"] == (
        exact_byte_binding_fields
    )
    for stage_action in catalog["actions"][:6]:
        assert "lifecycle_admission" in stage_action["optional_fields"]
        contract = stage_action["authority_boundary"]["lifecycle_admission_contract"]
        assert contract["capability_id"] == "opl_domain_lifecycle_admission.v1"
        assert contract["reactivation_receipt_output_field"] == "reactivation_receipt"
        assert contract["materialization_authorization_output_field"] == (
            "mas_lifecycle_cas_mutation_authorization"
        )
        assert list(contract["reactivation_request_input_field_map"]) == [
            "work_item_id",
            "reactivation_request",
            "authority_context",
            "work_item_identity",
            "user_authority",
            "reviewer_revision_intake",
            "current_lifecycle",
            "profile",
            "projection_inventory",
        ]
        assert contract["exact_byte_binding_fields"] == exact_byte_binding_fields
        assert len(contract["reactivation_projection_sources"]) == 8
