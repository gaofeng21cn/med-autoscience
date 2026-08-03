from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator
import pytest

from med_autoscience.authority_handlers.qualification_work_item_provisioning import (
    evaluate_qualification_work_item_provisioning_authority,
)


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY_RECORD = {
    "surface_kind": "mas_qualification_work_item_provisioning_authority",
    "schema_version": 1,
    "authority_ref": "mas-qualification-authority:full-vm-001",
    "domain_owner": "MedAutoScience",
    "domain_id": "medautoscience",
    "canonical_workspace_root": "/private/tmp/opl-full-vm/workspace",
    "qualification_scope": "standard_agent_full_vm_qualification",
    "issued_at": "2026-07-22T10:00:00Z",
    "single_use": True,
    "qualification_only": True,
    "provisions_work_item": True,
    "authorizes_stage_body": False,
    "authorizes_business_action": False,
    "authorizes_publication": False,
    "authorizes_submission": False,
    "provider_completion_is_domain_completion": False,
}


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _bound_json(record: dict[str, object], prefix: str) -> dict[str, object]:
    raw = _json_bytes(record)
    return {
        f"{prefix}_sha256": hashlib.sha256(raw).hexdigest(),
        f"{prefix}_bytes_base64": base64.b64encode(raw).decode("ascii"),
        f"{prefix}_byte_size": len(raw),
        "record": deepcopy(record),
    }


def _request(
    *,
    authority_record: dict[str, object] | None = None,
    workspace_index: dict[str, object] | None = None,
) -> dict[str, object]:
    record = deepcopy(authority_record or AUTHORITY_RECORD)
    request: dict[str, object] = {
        "surface_kind": (
            "mas_qualification_work_item_provisioning_authority_request"
        ),
        "schema_version": 1,
        "authority_context": {
            "action_id": (
                "qualification_work_item_provisioning_authority_evaluate"
            ),
            "handler_call_ref": "opl-handler-call:qualification-001",
            "owner_ledger_ref": "opl-owner-ledger:qualification-001",
        },
        "qualification_authority": _bound_json(record, "authority"),
        "current_workspace_index": {
            "exists": False,
            "workspace_index_ref": "workspace_index.json",
            "workspace_index_sha256": None,
            "workspace_index_bytes_base64": None,
            "workspace_index_byte_size": None,
            "record": None,
        },
    }
    if workspace_index is not None:
        request["current_workspace_index"] = {
            "exists": True,
            "workspace_index_ref": "workspace_index.json",
            **_bound_json(workspace_index, "workspace_index"),
        }
    return request


def _validator(filename: str) -> Draft202012Validator:
    schema = json.loads(
        (ROOT / "contracts/schemas/v2" / filename).read_text(encoding="utf-8")
    )
    return Draft202012Validator(schema)


def _operation_payload(result: dict[str, object], suffix: str) -> dict[str, object]:
    request = result["opl_host_materialization_request"]
    assert isinstance(request, dict)
    operation = next(
        item
        for item in request["operations"]
        if item["target_relative_path"].endswith(suffix)
    )
    raw = base64.b64decode(operation["replacement_bytes_base64"])
    assert operation["replacement_byte_size"] == len(raw)
    assert operation["replacement_sha256"] == (
        f"sha256:{hashlib.sha256(raw).hexdigest()}"
    )
    return json.loads(raw)


def test_absent_inventory_authorizes_exact_qualification_only_cas_bytes() -> None:
    request = _request()
    input_validator = _validator(
        "mas-qualification-work-item-provisioning-authority.input.schema.json"
    )
    output_validator = _validator(
        "mas-qualification-work-item-provisioning-authority.output.schema.json"
    )

    input_validator.validate(request)
    result = evaluate_qualification_work_item_provisioning_authority(request)
    output_validator.validate(result)

    assert result == evaluate_qualification_work_item_provisioning_authority(request)
    assert result["status"] == "authorized"
    authority_sha256 = request["qualification_authority"]["authority_sha256"]
    study_id = f"qualification-{authority_sha256}"
    study_root = f"studies/{study_id}"
    identity = result["study_identity"]
    assert identity == {
        "domain_owner": "MedAutoScience",
        "domain_id": "medautoscience",
        "canonical_workspace_root": "/private/tmp/opl-full-vm/workspace",
        "study_id": study_id,
        "canonical_study_root": study_root,
        "lifecycle_relative_path": f"{study_root}/control/lifecycle.json",
        "receipt_relative_path": (
            f"{study_root}/artifacts/controller/qualification/"
            "provisioning-receipt.json"
        ),
    }

    host_request = result["opl_host_materialization_request"]
    authorization = result[
        "mas_qualification_work_item_cas_mutation_authorization"
    ]
    assert len(host_request["operations"]) == 3
    assert host_request["capability_id"] == (
        "opl_domain_artifact_cas_materialization.v1"
    )
    assert host_request["authorization_ref"] == authorization["authorization_ref"]
    assert host_request["operations_sha256"] == authorization["operations_sha256"]
    assert host_request["materialization_scope_sha256"] == authorization[
        "materialization_scope_sha256"
    ]
    assert host_request["absent_relative_path_preconditions"] == sorted(
        [
            "workspace_index.json",
            f"{study_root}/control/lifecycle.json",
            (
                f"{study_root}/artifacts/controller/qualification/"
                "provisioning-receipt.json"
            ),
        ]
    )

    index = _operation_payload(result, "workspace_index.json")
    assert index["studies"] == [
        {
            "study_id": study_id,
            "canonical_study_root": study_root,
            "display_name": "Qualification work item",
            "status": "qualification_only",
            "current_stage_id": None,
            "current_stage_status": None,
            "package_status": "not_started",
            "lifecycle_ref": "control/lifecycle.json",
            "qualification_only": True,
            "stage_body_authorized": False,
            "business_action_authorized": False,
            "publication_authorized": False,
            "submission_authorized": False,
        }
    ]
    lifecycle = _operation_payload(result, "/control/lifecycle.json")
    assert lifecycle["study_id"] == study_id
    assert lifecycle["lifecycle_state"] == "active"
    assert lifecycle["generation"] == 1
    assert lifecycle["business_status"] == "qualification_only"
    assert lifecycle["current_stage_id"] is None
    assert lifecycle["current_stage_status"] is None
    for field in (
        "stage_body_authorized",
        "business_action_authorized",
        "publication_authorized",
        "submission_authorized",
    ):
        assert lifecycle[field] is False
        assert lifecycle["authority_boundary"][field] is False


def test_receipt_surface_and_exact_content_binding_are_closed_for_consumers() -> None:
    result = evaluate_qualification_work_item_provisioning_authority(_request())
    receipt = result["provisioning_receipt"]
    content = result["provisioning_receipt_content_binding"]
    authorization = result[
        "mas_qualification_work_item_cas_mutation_authorization"
    ]
    receipt_operation = next(
        item
        for item in result["opl_host_materialization_request"]["operations"]
        if item["target_relative_path"] == content["target_relative_path"]
    )

    assert receipt["surface_kind"] == (
        "mas_qualification_work_item_provisioning_receipt"
    )
    assert receipt["schema_version"] == 1
    assert receipt["domain_owner"] == "MedAutoScience"
    assert receipt["domain_id"] == "medautoscience"
    assert receipt["canonical_workspace_root"] == (
        "/private/tmp/opl-full-vm/workspace"
    )
    assert receipt["canonical_study_root"] == (
        f"studies/{receipt['study_id']}"
    )
    assert receipt["lifecycle_state"] == "active"
    assert receipt["lifecycle_generation"] == 1
    assert receipt["single_use"] is True
    assert receipt["qualification_only"] is True
    assert receipt["requires_opl_cas_materialization_receipt"] is True
    assert receipt["materialization_semantics"] == "journaled_all_or_rollback"
    for field in (
        "stage_body_authorized",
        "business_action_authorized",
        "publication_authorized",
        "submission_authorized",
    ):
        assert receipt[field] is False
        assert authorization[field] is False
    assert content["surface_kind"] == (
        "mas_qualification_work_item_provisioning_receipt_content_binding"
    )
    assert content["schema_version"] == 1
    assert content["receipt_ref"] == receipt["receipt_ref"]
    assert content["sha256"] == receipt_operation["replacement_sha256"]
    assert content["byte_size"] == receipt_operation["replacement_byte_size"]
    assert authorization["authority_receipt_ref"] == receipt["receipt_ref"]
    assert authorization["authority_receipt_content_sha256"] == content["sha256"]


def test_present_inventory_is_exact_cas_preserved_and_extended_once() -> None:
    current = {
        "surface_kind": "workspace_index",
        "schema_version": "mas.workspace_index.v1",
        "canonical_workspace_root": "/private/tmp/opl-full-vm/workspace",
        "host_extension": {"preserve": True},
        "studies": [
            {
                "study_id": "existing-study",
                "canonical_study_root": "studies/existing-study",
                "status": "active",
            }
        ],
    }
    request = _request(workspace_index=current)
    result = evaluate_qualification_work_item_provisioning_authority(request)

    assert result["status"] == "authorized"
    index_operation = next(
        item
        for item in result["opl_host_materialization_request"]["operations"]
        if item["target_relative_path"] == "workspace_index.json"
    )
    assert index_operation["precondition"] == {
        "kind": "existing_exact",
        "sha256": request["current_workspace_index"]["workspace_index_sha256"],
        "byte_size": request["current_workspace_index"]["workspace_index_byte_size"],
    }
    after = json.loads(base64.b64decode(index_operation["replacement_bytes_base64"]))
    assert after["host_extension"] == {"preserve": True}
    assert after["studies"][0] == current["studies"][0]
    assert len(after["studies"]) == 2


def test_exact_authority_bytes_deterministically_derive_identity() -> None:
    first_request = _request()
    first = evaluate_qualification_work_item_provisioning_authority(first_request)
    second = evaluate_qualification_work_item_provisioning_authority(first_request)
    changed_record = deepcopy(AUTHORITY_RECORD)
    changed_record["authority_ref"] = "mas-qualification-authority:full-vm-002"
    changed = evaluate_qualification_work_item_provisioning_authority(
        _request(authority_record=changed_record)
    )

    assert first == second
    assert first["study_identity"]["study_id"] == (
        "qualification-"
        f"{first_request['qualification_authority']['authority_sha256']}"
    )
    assert changed["study_identity"]["study_id"] != first["study_identity"][
        "study_id"
    ]


def test_inventory_collision_returns_typed_blocker_without_cas() -> None:
    initial_request = _request()
    digest = initial_request["qualification_authority"]["authority_sha256"]
    study_id = f"qualification-{digest}"
    current = {
        "surface_kind": "workspace_index",
        "schema_version": "mas.workspace_index.v1",
        "studies": [
            {
                "study_id": study_id,
                "canonical_study_root": f"studies/{study_id}",
            }
        ],
    }
    result = evaluate_qualification_work_item_provisioning_authority(
        _request(workspace_index=current)
    )
    _validator(
        "mas-qualification-work-item-provisioning-authority.output.schema.json"
    ).validate(result)

    assert result["status"] == "typed_blocker"
    assert result["typed_blocker"]["reason_code"] == (
        "qualification_authority_already_consumed"
    )
    assert result["provisioning_receipt"] is None
    assert result["provisioning_receipt_content_binding"] is None
    assert result["mas_qualification_work_item_cas_mutation_authorization"] is None
    assert result["opl_host_materialization_request"] is None


def test_noncanonical_existing_identity_mapping_is_invalid_host_input() -> None:
    current = {
        "surface_kind": "workspace_index",
        "schema_version": "mas.workspace_index.v1",
        "studies": [
            {
                "study_id": "other-study",
                "canonical_study_root": "studies/unrelated-study",
            }
        ],
    }
    result = evaluate_qualification_work_item_provisioning_authority(
        _request(workspace_index=current)
    )

    assert result["status"] == "invalid_host_input"
    assert result["opl_host_materialization_request"] is None


@pytest.mark.parametrize(
    "workspace_root",
    [
        "relative/workspace",
        "/",
        "/private/tmp/../workspace",
        "/private//tmp/workspace",
        "C:\\workspace",
    ],
)
def test_noncanonical_or_uncontained_workspace_root_fails_closed(
    workspace_root: str,
) -> None:
    authority = deepcopy(AUTHORITY_RECORD)
    authority["canonical_workspace_root"] = workspace_root
    result = evaluate_qualification_work_item_provisioning_authority(
        _request(authority_record=authority)
    )

    assert result["status"] == "invalid_host_input"
    assert result["opl_host_materialization_request"] is None
    assert result["mas_qualification_work_item_cas_mutation_authorization"] is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("single_use", False),
        ("qualification_only", False),
        ("provisions_work_item", False),
        ("authorizes_stage_body", True),
        ("authorizes_business_action", True),
        ("authorizes_publication", True),
        ("authorizes_submission", True),
        ("provider_completion_is_domain_completion", True),
    ],
)
def test_authority_cannot_expand_beyond_qualification_only(
    field: str, value: bool
) -> None:
    authority = deepcopy(AUTHORITY_RECORD)
    authority[field] = value
    request = _request(authority_record=authority)

    assert not _validator(
        "mas-qualification-work-item-provisioning-authority.input.schema.json"
    ).is_valid(request)
    result = evaluate_qualification_work_item_provisioning_authority(request)
    assert result["status"] == "invalid_host_input"
    assert result["opl_host_materialization_request"] is None


def test_exact_authority_hash_and_supplied_record_are_recomputed() -> None:
    mismatched_hash = _request()
    mismatched_hash["qualification_authority"]["authority_sha256"] = "0" * 64
    assert evaluate_qualification_work_item_provisioning_authority(mismatched_hash)[
        "status"
    ] == "invalid_host_input"

    mismatched_record = _request()
    mismatched_record["qualification_authority"]["record"][
        "authority_ref"
    ] = "mas-qualification-authority:forged"
    result = evaluate_qualification_work_item_provisioning_authority(
        mismatched_record
    )
    assert result["status"] == "invalid_host_input"
    assert "deep-equal" in result["error"]["detail"]


def test_output_schema_rejects_route_authorization_tampering() -> None:
    result = evaluate_qualification_work_item_provisioning_authority(_request())
    validator = _validator(
        "mas-qualification-work-item-provisioning-authority.output.schema.json"
    )
    validator.validate(result)

    for container, field in (
        ("provisioning_receipt", "stage_body_authorized"),
        ("provisioning_receipt", "business_action_authorized"),
        ("provisioning_receipt", "publication_authorized"),
        ("provisioning_receipt", "submission_authorized"),
        (
            "mas_qualification_work_item_cas_mutation_authorization",
            "stage_body_authorized",
        ),
    ):
        tampered = deepcopy(result)
        tampered[container][field] = True
        assert not validator.is_valid(tampered)


def test_handler_source_has_no_io_runtime_or_process_surface() -> None:
    source = (
        ROOT
        / "src/med_autoscience/authority_handlers/qualification_work_item_provisioning.py"
    ).read_text(encoding="utf-8")
    forbidden_fragments = (
        "import os",
        "import pathlib",
        "import socket",
        "import subprocess",
        "from pathlib",
        "open(",
        ".read_text(",
        ".read_bytes(",
        ".write_text(",
        ".write_bytes(",
        "Popen(",
        "run(",
    )
    assert all(fragment not in source for fragment in forbidden_fragments)
