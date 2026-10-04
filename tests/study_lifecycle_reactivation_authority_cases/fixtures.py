from __future__ import annotations

import base64
import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from med_autoscience.authority_handlers.study_lifecycle_reactivation import (
    _TARGET_ROLE_ORDER,
)

ROOT = Path(__file__).resolve().parents[2]
STUDY_ID = "001-dm-cvd-mortality-risk"


def _digest(name: str) -> str:
    return f"sha256:{hashlib.sha256(name.encode()).hexdigest()}"


def _json_bytes(record: dict[str, Any]) -> bytes:
    return json.dumps(
        record,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _json_fingerprint(value: Any) -> str:
    return f"sha256:{hashlib.sha256(_json_bytes(value)).hexdigest()}"


def _bind_json_record(
    target: dict[str, Any],
    *,
    bytes_field: str,
    byte_size_field: str,
    sha256_field: str,
) -> None:
    raw_bytes = _json_bytes(target["record"])
    target[bytes_field] = base64.b64encode(raw_bytes).decode("ascii")
    target[byte_size_field] = len(raw_bytes)
    target[sha256_field] = f"sha256:{hashlib.sha256(raw_bytes).hexdigest()}"


def _rebind_user_authority(request: dict[str, Any]) -> None:
    authority = request["user_authority"]
    _bind_json_record(
        authority,
        bytes_field="authority_bytes_base64",
        byte_size_field="authority_byte_size",
        sha256_field="authority_sha256",
    )
    request["reactivation_request"]["user_authority_sha256"] = authority[
        "authority_sha256"
    ]
    request["reviewer_revision_intake"]["record"]["user_authority_sha256"] = (
        authority["authority_sha256"]
    )
    _rebind_revision_intake(request)


def _rebind_revision_intake(request: dict[str, Any]) -> None:
    intake = request["reviewer_revision_intake"]
    _bind_json_record(
        intake,
        bytes_field="intake_bytes_base64",
        byte_size_field="intake_byte_size",
        sha256_field="intake_sha256",
    )
    request["reactivation_request"]["reviewer_revision_intake_sha256"] = intake[
        "intake_sha256"
    ]


def _rebind_current_lifecycle(request: dict[str, Any]) -> None:
    lifecycle = request["current_lifecycle"]
    _bind_json_record(
        lifecycle,
        bytes_field="lifecycle_bytes_base64",
        byte_size_field="lifecycle_byte_size",
        sha256_field="lifecycle_sha256",
    )
    reactivation = request["reactivation_request"]
    reactivation["current_lifecycle_sha256"] = lifecycle["lifecycle_sha256"]
    reactivation["observed_lifecycle_state"] = lifecycle["record"][
        "lifecycle_state"
    ]
    reactivation["observed_lifecycle_generation"] = lifecycle["record"][
        "generation"
    ]


def _rebind_projection_target(target: dict[str, Any]) -> None:
    _bind_json_record(
        target,
        bytes_field="bytes_base64",
        byte_size_field="byte_size",
        sha256_field="sha256",
    )


def _replace_bound_json_bytes(
    target: dict[str, Any],
    raw_bytes: bytes,
    *,
    bytes_field: str,
    byte_size_field: str,
    sha256_field: str,
) -> None:
    target[bytes_field] = base64.b64encode(raw_bytes).decode("ascii")
    target[byte_size_field] = len(raw_bytes)
    target[sha256_field] = f"sha256:{hashlib.sha256(raw_bytes).hexdigest()}"


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
    user_authority_ref = "file:///workspace/control/user-authority.json"
    revision_intake_ref = "file:///workspace/control/reviewer-revision-intake.json"
    profile_body = "developer_supervisor_mode: true\n"
    user_authority = {
        "authority_ref": user_authority_ref,
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
    }
    _bind_json_record(
        user_authority,
        bytes_field="authority_bytes_base64",
        byte_size_field="authority_byte_size",
        sha256_field="authority_sha256",
    )
    reviewer_revision_intake = {
        "intake_ref": revision_intake_ref,
        "record": {
            "surface_kind": "mas_reviewer_revision_task_intake",
            "schema_version": 1,
            "task_intake_kind": "reviewer_revision",
            "study_id": STUDY_ID,
            "status": "accepted",
            "user_authority_ref": user_authority_ref,
            "user_authority_sha256": user_authority["authority_sha256"],
            "recorded_at": "2026-07-21T01:00:00Z",
            "request_summary": "Revise the manuscript through MAS.",
            "revision_checklist_ref": (
                "file:///workspace/control/revision-checklist.json"
            ),
            "revision_checklist_sha256": _digest("revision-checklist"),
            "independent_review_packet_ref": (
                "file:///workspace/control/independent-review.json"
            ),
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
    }
    _bind_json_record(
        reviewer_revision_intake,
        bytes_field="intake_bytes_base64",
        byte_size_field="intake_byte_size",
        sha256_field="intake_sha256",
    )
    current_lifecycle = {
        "lifecycle_ref": lifecycle_ref,
        "record": deepcopy(lifecycle),
    }
    _bind_json_record(
        current_lifecycle,
        bytes_field="lifecycle_bytes_base64",
        byte_size_field="lifecycle_byte_size",
        sha256_field="lifecycle_sha256",
    )
    targets = [
        {
            "projection_id": "study_lifecycle_current",
            "root": "work_item",
            "relative_path": "control/lifecycle.json",
            "ref": lifecycle_ref,
            "record": deepcopy(lifecycle),
        },
        {
            "projection_id": "workspace_lifecycle_latest",
            "root": "workspace",
            "relative_path": "runtime/artifacts/study_lifecycle_control/latest.json",
            "ref": "file:///workspace/runtime/artifacts/study_lifecycle_control/latest.json",
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
            "record": _workspace_index(state),
        },
        {
            "projection_id": "submission_status",
            "root": "work_item",
            "relative_path": "submission/STATUS.json",
            "ref": f"file:///workspace/studies/{STUDY_ID}/submission/STATUS.json",
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
    for target in targets:
        _rebind_projection_target(target)
    return {
        "study_id": STUDY_ID,
        "reactivation_request": {
            "profile_ref": "file:///workspace/profile.yaml",
            "profile_sha256": _digest(profile_body),
            "user_authority_ref": user_authority_ref,
            "user_authority_sha256": user_authority["authority_sha256"],
            "reviewer_revision_intake_ref": revision_intake_ref,
            "reviewer_revision_intake_sha256": reviewer_revision_intake[
                "intake_sha256"
            ],
            "current_lifecycle_ref": lifecycle_ref,
            "current_lifecycle_sha256": current_lifecycle["lifecycle_sha256"],
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
            "requested_action_id": "baseline_and_evidence_setup",
            "requested_run_id": "stage-run-001",
            "original_invocation_sha256": _digest("original-invocation"),
        },
        "study_identity": {
            "study_id": STUDY_ID,
            "work_item_root_ref": f"file:///workspace/studies/{STUDY_ID}",
            "lifecycle_ref": lifecycle_ref,
            "descriptor_domain_id": "medautoscience",
        },
        "current_lifecycle": current_lifecycle,
        "user_authority": user_authority,
        "reviewer_revision_intake": reviewer_revision_intake,
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


def _request_with_all_optional_projections() -> dict[str, Any]:
    request = _request()
    targets = {
        item["projection_id"]: item
        for item in request["projection_inventory"]["targets"]
    }
    targets.update(
        {
            "workspace_studies_index": {
                "projection_id": "workspace_studies_index",
                "root": "workspace",
                "relative_path": "reports/studies_index.json",
                "ref": "file:///workspace/reports/studies_index.json",
                "sha256": _digest("workspace-studies-index-g1"),
                "byte_size": 1200,
                "record": _workspace_index("paused"),
            },
            "workspace_latest_status": {
                "projection_id": "workspace_latest_status",
                "root": "workspace",
                "relative_path": "reports/latest_status.json",
                "ref": "file:///workspace/reports/latest_status.json",
                "sha256": _digest("workspace-latest-status-g1"),
                "byte_size": 800,
                "record": {
                    "surface_kind": "workspace_latest_status",
                    "schema_version": 1,
                    "status_counts": {"paused": 1},
                    "next_required_actions": ["wait_for_explicit_user_wakeup"],
                    "recorded_at": "2026-07-20T00:00:00Z",
                },
            },
            "publication_current_package_status": {
                "projection_id": "publication_current_package_status",
                "root": "work_item",
                "relative_path": "publication/current_package/STATUS.json",
                "ref": (
                    f"file:///workspace/studies/{STUDY_ID}/"
                    "publication/current_package/STATUS.json"
                ),
                "sha256": _digest("publication-current-package-status-g1"),
                "byte_size": 500,
                "record": {
                    "surface_kind": "study_current_package_status",
                    "schema_version": 1,
                    "lifecycle_state": "paused",
                    "status": "not_ready",
                    "submission_ready": False,
                    "promotion_allowed": False,
                    "reason": "The user paused this study.",
                    "recorded_at": "2026-07-20T00:00:00Z",
                },
            },
            "stage_index": {
                "projection_id": "stage_index",
                "root": "work_item",
                "relative_path": "control/stage_index.json",
                "ref": (
                    f"file:///workspace/studies/{STUDY_ID}/control/stage_index.json"
                ),
                "sha256": _digest("stage-index-g1"),
                "byte_size": 700,
                "record": {
                    "surface_kind": "mas_stage_index",
                    "schema_version": 1,
                    "study_id": STUDY_ID,
                    "lifecycle_state": "paused",
                    "stages": [],
                },
            },
        }
    )
    request["projection_inventory"]["targets"] = [
        targets[role] for role in _TARGET_ROLE_ORDER
    ]
    for target in request["projection_inventory"]["targets"]:
        _rebind_projection_target(target)
    request["projection_inventory"]["absent_optional_projection_ids"] = []
    return request


def _projection_target(
    request: dict[str, Any], projection_id: str
) -> dict[str, Any]:
    return next(
        target
        for target in request["projection_inventory"]["targets"]
        if target["projection_id"] == projection_id
    )


def _operation_payload(operation: dict[str, Any]) -> dict[str, Any]:
    return json.loads(base64.b64decode(operation["replacement_bytes_base64"]))


def _request_with_current_multistudy_projection_shape() -> dict[str, Any]:
    request = _request_with_all_optional_projections()
    other_study_id = "004-dpcc-longitudinal-care-inertia-intensification-gap"
    other_lifecycle = _lifecycle("delivered_paused")
    other_lifecycle["study_id"] = other_study_id

    workspace_lifecycle = _projection_target(
        request, "workspace_lifecycle_latest"
    )["record"]
    workspace_lifecycle["recorded_at"] = "2026-07-20T00:30:00Z"
    workspace_lifecycle["status_counts"] = {
        "paused": 1,
        "delivered_paused": 1,
    }
    workspace_lifecycle["changed_study_id"] = other_study_id
    workspace_lifecycle["changed_generation"] = other_lifecycle["generation"]
    workspace_lifecycle["studies"].append(other_lifecycle)

    for role in ("workspace_index", "workspace_studies_index"):
        workspace_index = _projection_target(request, role)["record"]
        workspace_index["status_counts"] = {
            "paused": 1,
            "delivered_paused": 1,
        }
        workspace_index["studies"][0].pop("submission_ready")
        other_study = _workspace_index("delivered_paused")["studies"][0]
        other_study["study_id"] = other_study_id
        workspace_index["studies"].append(other_study)

    latest_status = _projection_target(request, "workspace_latest_status")["record"]
    latest_status["schema_version"] = "mas.workspace_status.v1"
    latest_status["status_counts"] = {
        "paused": 1,
        "delivered_paused": 1,
    }
    latest_status["next_required_actions"] = [
        "wait_for_explicit_user_wakeup"
    ]

    submission_status = _projection_target(request, "submission_status")["record"]
    submission_status.clear()
    submission_status.update(
        {
            "authority": False,
            "candidate_generation": "v3r6",
            "mas_owner_receipt_issued": False,
            "package_stage": "author_review_package",
            "reason": "registered owner facts and submission metadata remain open",
            "schema_version": "study001-formal-sci-package-status.v1",
            "status": "not_ready",
            "submission_ready": False,
        }
    )

    stage_index = _projection_target(request, "stage_index")["record"]
    stage_index.pop("surface_kind")
    stage_index["schema_version"] = "mas.study_stage_index.v1"

    for target in request["projection_inventory"]["targets"]:
        _rebind_projection_target(target)
    return request


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
