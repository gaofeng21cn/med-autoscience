from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, ValidationError

from med_autoscience.authority_handlers.study_lifecycle_reactivation import (
    evaluate_study_lifecycle_reactivation_authority,
)


ROOT = Path(__file__).resolve().parents[1]
STUDY_ID = "001-dm-cvd-mortality-risk"


def _digest(name: str) -> str:
    return f"sha256:{hashlib.sha256(name.encode()).hexdigest()}"


def _exact(kind: str, name: str) -> dict[str, Any]:
    return {
        "kind": kind,
        "ref": f"{kind}://{name}",
        "size_bytes": 100 + len(name),
        "sha256": _digest(f"{kind}:{name}"),
    }


def _typed(kind: str, name: str) -> dict[str, str]:
    return {
        "kind": kind,
        "ref": f"{kind}://{name}",
        "sha256": _digest(f"{kind}:{name}"),
    }


def _lifecycle(state: str = "paused") -> dict[str, Any]:
    return {
        "authority_boundary": {
            "domain_truth": True,
            "opl_consumption": "read_only_projection",
            "paper_body_mutated": False,
            "publication_eval_mutated": False,
            "runtime_or_telemetry_can_override": False,
            "submission_package_promoted": False,
            "truth_owner": "MedAutoScience",
        },
        "business_status": state,
        "current_stage_id": None,
        "current_stage_policy": "no_current_stage_while_inactive",
        "current_stage_status": None,
        "evidence_refs": [],
        "generation": 1,
        "lifecycle_ref": "control/lifecycle.json",
        "lifecycle_state": state,
        "materialized_at": "2026-07-20T00:00:00Z",
        "milestone_package_delivered": state == "delivered_paused",
        "next_action": {
            "surface_kind": "mas_lifecycle_action",
            "action_id": "wait_for_explicit_user_wakeup",
            "action_type": "user_action",
            "owner": "user",
            "status": state,
            "summary": "Wait for explicit user wakeup.",
        },
        "package_status": (
            "milestone_delivered" if state == "delivered_paused" else "not_ready"
        ),
        "reason_code": "user_paused",
        "reason_summary": "The user paused this study.",
        "recorded_at": "2026-07-20T00:00:00Z",
        "resume_policy": {
            "policy_id": "explicit_user_wakeup",
            "auto_resume_allowed": False,
            "explicit_user_wakeup_required": True,
            "allow_stopped_relaunch_required": state == "stopped",
        },
        "schema_version": "mas.study_lifecycle_control.v1",
        "source_kind": "explicit_user_truth",
        "source_ref": "user-authority://pause",
        "study_id": STUDY_ID,
        "submission_ready": False,
        "surface_kind": "study_lifecycle_control",
    }


def _workspace_index(state: str) -> dict[str, Any]:
    return {
        "schema_version": "mas.workspace_index.v1",
        "surface_kind": "workspace_index",
        "recorded_at": "2026-07-20T00:00:00Z",
        "status_counts": {state: 1},
        "studies": [
            {
                "study_id": STUDY_ID,
                "status": state,
                "business_status": state,
                "lifecycle_state": state,
                "auto_resume_allowed": False,
                "lifecycle_reason_code": "user_paused",
                "lifecycle_reason_summary": "The user paused this study.",
                "next_action": {
                    "action_id": "wait_for_explicit_user_wakeup",
                    "owner": "user",
                },
                "resume_policy": {"auto_resume_allowed": False},
                "package_status": "not_ready",
                "submission_ready": False,
            }
        ],
    }


def _request(state: str = "paused") -> dict[str, Any]:
    lifecycle = _lifecycle(state)
    lifecycle_ref = f"file:///workspace/studies/{STUDY_ID}/control/lifecycle.json"
    lifecycle_sha256 = _digest("study-001-lifecycle-g1")
    user_authority_ref = "file:///workspace/control/user-authority.json"
    user_authority_sha256 = _digest("user-wakeup-001")
    revision_intake_ref = "file:///workspace/control/reviewer-revision-intake.json"
    revision_intake_sha256 = _digest("revision-001")
    profile_body = "developer_supervisor_mode: true\n"
    targets = [
        {
            "projection_id": "study_lifecycle_current",
            "root": "work_item",
            "relative_path": "control/lifecycle.json",
            "ref": lifecycle_ref,
            "sha256": lifecycle_sha256,
            "byte_size": 1100,
            "record": deepcopy(lifecycle),
        },
        {
            "projection_id": "workspace_lifecycle_latest",
            "root": "workspace",
            "relative_path": "runtime/artifacts/study_lifecycle_control/latest.json",
            "ref": "file:///workspace/runtime/artifacts/study_lifecycle_control/latest.json",
            "sha256": _digest("workspace-lifecycle-g1"),
            "byte_size": 1500,
            "record": {
                "schema_version": "mas.workspace_study_lifecycle_control.v1",
                "surface_kind": "workspace_study_lifecycle_control",
                "workspace_name": "dm-cvd-mortality-risk",
                "recorded_at": "2026-07-20T00:00:00Z",
                "status_counts": {state: 1},
                "changed_study_id": STUDY_ID,
                "changed_generation": 1,
                "studies": [deepcopy(lifecycle)],
            },
        },
        {
            "projection_id": "workspace_index",
            "root": "workspace",
            "relative_path": "workspace_index.json",
            "ref": "file:///workspace/workspace_index.json",
            "sha256": _digest("workspace-index-g1"),
            "byte_size": 1200,
            "record": _workspace_index(state),
        },
        {
            "projection_id": "submission_status",
            "root": "work_item",
            "relative_path": "submission/STATUS.json",
            "ref": f"file:///workspace/studies/{STUDY_ID}/submission/STATUS.json",
            "sha256": _digest("submission-status-g1"),
            "byte_size": 500,
            "record": {
                "surface_kind": "study_current_package_status",
                "schema_version": 1,
                "lifecycle_state": state,
                "status": "not_ready",
                "submission_ready": False,
                "promotion_allowed": False,
                "publication_verdict": "not_ready",
                "reason": "The user paused this study.",
                "recorded_at": "2026-07-20T00:00:00Z",
            },
        },
    ]
    return {
        "study_id": STUDY_ID,
        "reactivation_request": {
            "profile_ref": "file:///workspace/profile.yaml",
            "profile_sha256": _digest(profile_body),
            "user_authority_ref": user_authority_ref,
            "user_authority_sha256": user_authority_sha256,
            "reviewer_revision_intake_ref": revision_intake_ref,
            "reviewer_revision_intake_sha256": revision_intake_sha256,
            "current_lifecycle_ref": lifecycle_ref,
            "current_lifecycle_sha256": lifecycle_sha256,
            "observed_lifecycle_state": state,
            "observed_lifecycle_generation": 1,
            "explicit_user_wakeup": True,
            "allow_stopped_relaunch": state == "stopped",
            "requested_at": "2026-07-21T01:00:00Z",
            "reason_code": "reviewer_revision_reactivation",
            "reason_summary": "The user explicitly reactivated this study for revision.",
        },
        "authority_context": {
            "handler_call_ref": "opl://standard-agent-action-run/reactivate-001",
            "owner_ledger_ref": "file:///workspace/control/opl/owner-ledger.json",
            "original_admission_request_ref": "file:///workspace/control/opl/admission.json",
            "original_admission_request_sha256": _digest("admission-request-001"),
            "admission_scope_id": "admission-scope-001",
            "requested_action_id": "review_and_quality_gate",
            "requested_run_id": "stage-run-001",
            "original_invocation_sha256": _digest("original-invocation"),
        },
        "study_identity": {
            "study_id": STUDY_ID,
            "work_item_root_ref": f"file:///workspace/studies/{STUDY_ID}",
            "lifecycle_ref": lifecycle_ref,
            "descriptor_domain_id": "medautoscience",
        },
        "current_lifecycle": {
            "lifecycle_ref": lifecycle_ref,
            "lifecycle_sha256": lifecycle_sha256,
            "record": deepcopy(lifecycle),
        },
        "user_authority": {
            "authority_ref": user_authority_ref,
            "authority_sha256": user_authority_sha256,
            "record": {
                "surface_kind": "mas_explicit_user_authority_evidence",
                "schema_version": 1,
                "study_id": STUDY_ID,
                "task_intake_kind": "reviewer_revision",
                "status": "accepted",
                "explicit_user_wakeup": True,
                "allow_stopped_relaunch": state == "stopped",
                "recorded_at": "2026-07-21T01:00:00Z",
                "source_kind": "explicit_user_instruction",
                "source_ref": "codex-task://dm-cvd-revision",
                "instruction_text": "Revise Study 001 through MAS.",
                "instruction_sha256": _digest("Revise Study 001 through MAS."),
                "source_owner": "user",
                "record_owner": "MedAutoScience",
                "owner_receipt": False,
            },
        },
        "reviewer_revision_intake": {
            "intake_ref": revision_intake_ref,
            "intake_sha256": revision_intake_sha256,
            "record": {
                "surface_kind": "mas_reviewer_revision_task_intake",
                "schema_version": 1,
                "task_intake_kind": "reviewer_revision",
                "study_id": STUDY_ID,
                "status": "accepted",
                "user_authority_ref": user_authority_ref,
                "user_authority_sha256": user_authority_sha256,
                "recorded_at": "2026-07-21T01:00:00Z",
                "request_summary": "Revise the manuscript through MAS.",
                "revision_checklist_ref": "file:///workspace/control/revision-checklist.json",
                "revision_checklist_sha256": _digest("revision-checklist"),
                "independent_review_packet_ref": "file:///workspace/control/independent-review.json",
                "independent_review_packet_sha256": _digest("independent-review"),
                "first_owning_stage_id": "baseline_and_evidence_setup",
                "allowed_revision_scope": [
                    "baseline_and_evidence",
                    "statistical_analysis",
                    "manuscript_and_displays",
                    "independent_re_review",
                ],
                "record_owner": "MedAutoScience",
                "source_owner": "user",
                "owner_receipt": False,
            },
        },
        "profile": {
            "profile_ref": "file:///workspace/profile.yaml",
            "profile_sha256": _digest(profile_body),
            "profile_byte_size": len(profile_body.encode("utf-8")),
            "profile_body_utf8": profile_body,
        },
        "projection_inventory": {
            "discovery_complete": True,
            "targets": targets,
            "absent_optional_projection_ids": [
                "publication_current_package_status",
                "stage_index",
                "workspace_latest_status",
                "workspace_studies_index",
            ],
        },
    }


def _validator(name: str) -> Draft202012Validator:
    schema = json.loads(
        (ROOT / "contracts/schemas/v2" / name).read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _stage_action_input(lifecycle_admission: dict[str, Any]) -> dict[str, Any]:
    return {
        "workspace_root": "/tmp/dm-cvd-mortality-risk",
        "study_id": STUDY_ID,
        "lifecycle_admission": lifecycle_admission,
    }


def test_paused_reactivation_returns_deterministic_atomic_cas_authority() -> None:
    request = _request()
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
    assert receipt["requested_action_id"] == "review_and_quality_gate"
    assert receipt["materialization_semantics"] == "journaled_all_or_rollback"

    host_request = result["opl_host_materialization_request"]
    authorization = result["mas_lifecycle_cas_mutation_authorization"]
    assert host_request["capability_id"] == "opl_domain_artifact_cas_materialization.v1"
    assert authorization["operations_sha256"] == host_request["operations_sha256"]
    assert host_request["version"] == "opl-domain-artifact-cas-materialization.v1"
    assert host_request["authorization_ref"] == authorization["authorization_ref"]
    assert authorization["authority_receipt_ref"] == receipt["receipt_ref"]

    operations = host_request["operations"]
    assert len(operations) == 7
    paths = {operation["target_relative_path"] for operation in operations}
    assert f"studies/{STUDY_ID}/control/lifecycle.json" in paths
    assert f"studies/{STUDY_ID}/submission/STATUS.json" in paths
    assert any("lifecycle_control/history/" in path for path in paths)
    assert any("reactivation_receipts/" in path for path in paths)
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
    assert "paused" not in submission["reason"].lower()
    assert submission["recorded_at"] == "2026-07-21T01:00:00Z"


def test_stopped_reactivation_requires_separate_relaunch_authority() -> None:
    request = _request("stopped")
    request["reactivation_request"]["allow_stopped_relaunch"] = False
    request["user_authority"]["record"]["allow_stopped_relaunch"] = False

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

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "typed_blocker"
    assert result["typed_blocker"]["reason_code"] == (
        "lifecycle_projection_currentness_mismatch"
    )
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
    request["user_authority"]["record"]["explicit_user_wakeup"] = False

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "invalid_host_input"
    assert "explicit_user_wakeup must match" in result["error"]["detail"]


def test_user_instruction_digest_is_recomputed_by_handler() -> None:
    request = _request()
    request["user_authority"]["record"]["instruction_text"] = "Different instruction."

    result = evaluate_study_lifecycle_reactivation_authority(request)

    assert result["status"] == "invalid_host_input"
    assert "does not match normalized instruction_text" in result["error"]["detail"]


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
    assert action["authority_boundary"]["host_materialization_contract"] == {
        "capability_id": "opl_domain_artifact_cas_materialization.v1",
        "request_output_field": "opl_host_materialization_request",
        "authorization_output_field": "mas_lifecycle_cas_mutation_authorization",
    }
    assert len(stage_schema["$defs"]["lifecycle_admission"]["oneOf"]) == 2
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
        assert len(contract["reactivation_projection_sources"]) == 8
