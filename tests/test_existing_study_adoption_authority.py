from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
import pytest


ROOT = Path(__file__).resolve().parents[1]
STUDY_ID = "tcm-multidisease-staged-agent-v1"
WORKSPACE_ROOT = "/workspace"
MAS_INVENTORY_PATH = "runtime/artifacts/mas_workspace_index/latest.json"
WORKSPACE_LIFECYCLE_PATH = (
    "runtime/artifacts/study_lifecycle_control/latest.json"
)


def _json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: str) -> str:
    return f"sha256:{hashlib.sha256(value.encode()).hexdigest()}"


def _bound_json(
    record: dict[str, Any],
    *,
    ref_field: str,
    ref: str,
    sha256_field: str,
    bytes_field: str,
    byte_size_field: str,
) -> dict[str, Any]:
    raw = _json_bytes(record)
    return {
        ref_field: ref,
        sha256_field: f"sha256:{hashlib.sha256(raw).hexdigest()}",
        bytes_field: base64.b64encode(raw).decode("ascii"),
        byte_size_field: len(raw),
        "record": deepcopy(record),
    }


def _absent_projection(ref_field: str, ref: str) -> dict[str, Any]:
    prefix = ref_field.removesuffix("_ref")
    return {
        "exists": False,
        ref_field: ref,
        f"{prefix}_sha256": None,
        f"{prefix}_bytes_base64": None,
        f"{prefix}_byte_size": None,
        "record": None,
    }


def _present_projection(
    record: dict[str, Any],
    *,
    ref_field: str,
    ref: str,
) -> dict[str, Any]:
    prefix = ref_field.removesuffix("_ref")
    return {
        "exists": True,
        **_bound_json(
            record,
            ref_field=ref_field,
            ref=ref,
            sha256_field=f"{prefix}_sha256",
            bytes_field=f"{prefix}_bytes_base64",
            byte_size_field=f"{prefix}_byte_size",
        ),
    }


def _request(
    *,
    mas_inventory: dict[str, Any] | None = None,
    workspace_lifecycle: dict[str, Any] | None = None,
) -> dict[str, Any]:
    recorded_at = "2026-08-02T09:30:00Z"
    user_authority_ref = (
        "file:///workspace/control/reviewer-revision-user-authority.json"
    )
    user_authority_record = {
        "surface_kind": "mas_explicit_user_authority_evidence",
        "schema_version": 1,
        "study_id": STUDY_ID,
        "task_intake_kind": "reviewer_revision",
        "status": "accepted",
        "explicit_user_wakeup": True,
        "allow_stopped_relaunch": True,
        "recorded_at": recorded_at,
        "source_kind": "explicit_user_instruction",
        "source_ref": "codex-task://existing-study-adoption-20260802",
        "instruction_text": "Adopt the existing study into MAS before revision.",
        "instruction_sha256": _digest(
            "Adopt the existing study into MAS before revision."
        ),
        "source_owner": "user",
        "record_owner": "MedAutoScience",
        "owner_receipt": False,
    }
    evidence_ref = (
        f"file:///workspace/studies/{STUDY_ID}/artifacts/truth/latest.json"
    )
    evidence_record = {
        "surface_kind": "mas_existing_study_adoption_evidence",
        "schema_version": 1,
        "study_id": STUDY_ID,
        "canonical_study_root": f"studies/{STUDY_ID}",
        "display_name": "Decoupled TCM staged-agent benchmark",
        "evidence_kind": "persisted_existing_study",
        "observed_at": "2026-08-02T09:19:06Z",
        "evidence_refs": [
            {
                "kind": "legacy_truth_projection",
                "ref": evidence_ref,
                "sha256": _digest("legacy-truth-projection"),
            }
        ],
        "qualification_only": False,
        "authorizes_stage_body": False,
        "authorizes_publication": False,
        "authorizes_submission": False,
    }
    topology_record = {
        "surface_kind": "opl_workspace_index",
        "version": "workspace-index.v1",
        "workspace_id": "decoupled_tcm_pilot",
        "workspace_path": WORKSPACE_ROOT,
        "agent": {"agent_id": "mas"},
        "projects": [
            {
                "project_id": STUDY_ID,
                "project_root": f"projects/{STUDY_ID}",
            }
        ],
    }
    return {
        "surface_kind": "mas_study_work_item_adoption_authority_request",
        "schema_version": 1,
        "authority_context": {
            "action_id": "study_work_item_adoption_authority_evaluate",
            "handler_call_ref": "opl-handler-call:study-adoption-001",
            "owner_ledger_ref": "opl-owner-ledger:study-adoption-001",
        },
        "adoption_authority": {
            "user_authority": _bound_json(
                user_authority_record,
                ref_field="authority_ref",
                ref=user_authority_ref,
                sha256_field="authority_sha256",
                bytes_field="authority_bytes_base64",
                byte_size_field="authority_byte_size",
            ),
            "current_opl_topology_inventory": _bound_json(
                topology_record,
                ref_field="topology_ref",
                ref="file:///workspace/workspace_index.json",
                sha256_field="topology_sha256",
                bytes_field="topology_bytes_base64",
                byte_size_field="topology_byte_size",
            ),
        },
        "existing_study_identity": {
            "study_id": STUDY_ID,
            "canonical_workspace_root": WORKSPACE_ROOT,
            "canonical_study_root": f"studies/{STUDY_ID}",
            "display_name": "Decoupled TCM staged-agent benchmark",
            **_bound_json(
                evidence_record,
                ref_field="evidence_ref",
                ref=evidence_ref,
                sha256_field="evidence_sha256",
                bytes_field="evidence_bytes_base64",
                byte_size_field="evidence_byte_size",
            ),
        },
        "current_mas_workspace_index": (
            _absent_projection("mas_workspace_index_ref", MAS_INVENTORY_PATH)
            if mas_inventory is None
            else _present_projection(
                mas_inventory,
                ref_field="mas_workspace_index_ref",
                ref=MAS_INVENTORY_PATH,
            )
        ),
        "current_workspace_lifecycle": (
            _absent_projection(
                "workspace_lifecycle_ref", WORKSPACE_LIFECYCLE_PATH
            )
            if workspace_lifecycle is None
            else _present_projection(
                workspace_lifecycle,
                ref_field="workspace_lifecycle_ref",
                ref=WORKSPACE_LIFECYCLE_PATH,
            )
        ),
    }


def _handler():
    module = importlib.import_module(
        "med_autoscience.authority_handlers.existing_study_adoption"
    )
    return module.evaluate_study_work_item_adoption_authority


def _validator(filename: str) -> Draft202012Validator:
    schema = json.loads(
        (ROOT / "contracts/schemas/v2" / filename).read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _operation_payload(result: dict[str, Any], path: str) -> dict[str, Any]:
    operation = next(
        item
        for item in result["opl_host_materialization_request"]["operations"]
        if item["target_relative_path"] == path
    )
    raw = base64.b64decode(operation["replacement_bytes_base64"])
    assert operation["replacement_byte_size"] == len(raw)
    assert operation["replacement_sha256"] == (
        f"sha256:{hashlib.sha256(raw).hexdigest()}"
    )
    return json.loads(raw)


def test_contract_registers_private_existing_study_adoption_and_separate_inventory() -> None:
    catalog = json.loads(
        (ROOT / "contracts/action_catalog.json").read_text(encoding="utf-8")
    )
    registry = json.loads(
        (ROOT / "contracts/domain_handler_registry.json").read_text(
            encoding="utf-8"
        )
    )
    descriptor = json.loads(
        (ROOT / "contracts/domain_descriptor.json").read_text(encoding="utf-8")
    )
    action = next(
        item
        for item in catalog["actions"]
        if item["action_id"] == "study_work_item_adoption_authority_evaluate"
    )

    assert action["execution_binding"] == {
        "kind": "handler_ref",
        "handler_ref": "handler:mas.study-work-item-adoption-authority-evaluate",
    }
    assert action["execution_scope"] == {"kind": "none"}
    assert all(value is None for value in action["supported_surfaces"].values())
    assert action["authority_boundary"]["public_action"] is False
    assert action["authority_boundary"]["authorizes_publication"] is False
    assert action["authority_boundary"]["authorizes_submission"] is False
    assert {
        item["handler_id"] for item in registry["handlers"]
    } >= {"mas.study-work-item-adoption-authority-evaluate"}

    inventory = descriptor["standard_agent_interface"]["inventory_projection"]
    assert inventory["relative_path"] == MAS_INVENTORY_PATH
    assert inventory["items_pointer"] == "/studies"
    assert descriptor["work_item_scope_binding"]["inventory"]["ref"] == (
        f"{MAS_INVENTORY_PATH}#/studies"
    )
    serialized = json.dumps(
        {
            "catalog": catalog,
            "descriptor": descriptor,
            "reactivation": json.loads(
                (
                    ROOT / "contracts/study_lifecycle_reactivation_contract.json"
                ).read_text(encoding="utf-8")
            ),
            "qualification": json.loads(
                (
                    ROOT
                    / "contracts/qualification_work_item_provisioning_contract.json"
                ).read_text(encoding="utf-8")
            ),
        },
        sort_keys=True,
    )
    assert '"relative_path": "workspace_index.json"' not in serialized
    assert '"workspace_index_target": "workspace_index.json"' not in serialized


def test_absent_domain_projections_authorize_exact_atomic_adoption_bytes() -> None:
    request = _request()
    input_validator = _validator(
        "mas-existing-study-adoption-authority.input.schema.json"
    )
    output_validator = _validator(
        "mas-existing-study-adoption-authority.output.schema.json"
    )
    input_validator.validate(request)

    result = _handler()(request)
    output_validator.validate(result)
    assert result == _handler()(request)
    assert result["status"] == "authorized"

    host_request = result["opl_host_materialization_request"]
    authorization = result[
        "mas_study_work_item_adoption_cas_mutation_authorization"
    ]
    assert host_request["capability_id"] == (
        "opl_domain_artifact_cas_materialization.v1"
    )
    assert host_request["authorization_ref"] == authorization["authorization_ref"]
    assert host_request["operations_sha256"] == authorization["operations_sha256"]
    assert host_request["materialization_scope_sha256"] == authorization[
        "materialization_scope_sha256"
    ]
    paths = [
        item["target_relative_path"] for item in host_request["operations"]
    ]
    assert len(paths) == len(set(paths)) == 8
    assert "workspace_index.json" not in paths
    assert paths == [
        MAS_INVENTORY_PATH,
        WORKSPACE_LIFECYCLE_PATH,
        f"studies/{STUDY_ID}/control/lifecycle.json",
        f"studies/{STUDY_ID}/submission/STATUS.json",
        (
            f"studies/{STUDY_ID}/artifacts/controller/adoption/"
            "provisioning-receipt.json"
        ),
        (
            f"studies/{STUDY_ID}/artifacts/controller/lifecycle_control/history/"
            "20260802T093000Z-g0001.json"
        ),
        (
            f"studies/{STUDY_ID}/artifacts/controller/lifecycle_control/history/"
            "20260802T093000Z-g0001-adoption-receipt.json"
        ),
        (
            "runtime/artifacts/study_lifecycle_control/history/"
            f"20260802T093000Z-{STUDY_ID}-g0001.json"
        ),
    ]
    assert host_request["absent_relative_path_preconditions"] == sorted(paths)

    lifecycle = _operation_payload(
        result, f"studies/{STUDY_ID}/control/lifecycle.json"
    )
    assert lifecycle["surface_kind"] == "study_lifecycle_control"
    assert lifecycle["schema_version"] == "mas.study_lifecycle_control.v1"
    assert lifecycle["study_id"] == STUDY_ID
    assert lifecycle["lifecycle_state"] == "delivered_paused"
    assert lifecycle["business_status"] == "delivered_paused"
    assert lifecycle["generation"] == 1
    assert lifecycle["current_stage_id"] is None
    assert lifecycle["current_stage_status"] is None
    assert lifecycle["submission_ready"] is False
    assert lifecycle["milestone_package_delivered"] is True
    assert lifecycle["resume_policy"]["explicit_user_wakeup_required"] is True

    inventory = _operation_payload(result, MAS_INVENTORY_PATH)
    assert inventory["surface_kind"] == "mas_workspace_index"
    assert inventory["schema_version"] == "mas.workspace_index.v1"
    assert inventory["status_counts"] == {"delivered_paused": 1}
    assert inventory["studies"][0]["study_id"] == STUDY_ID
    assert inventory["studies"][0]["canonical_study_root"] == (
        f"studies/{STUDY_ID}"
    )

    workspace_lifecycle = _operation_payload(
        result, WORKSPACE_LIFECYCLE_PATH
    )
    assert workspace_lifecycle["surface_kind"] == (
        "workspace_study_lifecycle_control"
    )
    assert workspace_lifecycle["changed_study_id"] == STUDY_ID
    assert workspace_lifecycle["changed_generation"] == 1
    assert workspace_lifecycle["studies"] == [lifecycle]

    submission = _operation_payload(
        result, f"studies/{STUDY_ID}/submission/STATUS.json"
    )
    assert submission["submission_ready"] is False
    assert submission["promotion_allowed"] is False
    assert submission["publication_verdict"] == "not_ready"


def test_adoption_receipt_and_authorization_never_grant_stage_or_submission() -> None:
    result = _handler()(_request())
    receipt = result["adoption_receipt"]
    content = result["adoption_receipt_content_binding"]
    authorization = result[
        "mas_study_work_item_adoption_cas_mutation_authorization"
    ]

    assert receipt["surface_kind"] == "mas_study_work_item_adoption_receipt"
    assert receipt["lifecycle_state"] == "delivered_paused"
    assert receipt["lifecycle_generation"] == 1
    assert receipt["qualification_only"] is False
    assert receipt["single_use"] is True
    assert receipt["requires_opl_cas_materialization_receipt"] is True
    assert receipt["materialization_semantics"] == "journaled_all_or_rollback"
    for field in (
        "authorizes_stage_body",
        "authorizes_business_action",
        "authorizes_publication",
        "authorizes_submission",
    ):
        assert receipt[field] is False
        assert authorization[field] is False
    assert content["receipt_ref"] == receipt["receipt_ref"]
    assert authorization["authority_receipt_ref"] == receipt["receipt_ref"]
    assert authorization["authority_receipt_content_sha256"] == content["sha256"]


def test_present_domain_inventory_is_exact_cas_extended_without_touching_opl_topology() -> None:
    other_id = "existing-study"
    other_lifecycle = {
        "surface_kind": "study_lifecycle_control",
        "schema_version": "mas.study_lifecycle_control.v1",
        "study_id": other_id,
        "lifecycle_ref": "control/lifecycle.json",
        "lifecycle_state": "paused",
        "business_status": "paused",
        "generation": 2,
        "recorded_at": "2026-08-01T00:00:00Z",
        "materialized_at": "2026-08-01T00:00:00Z",
        "reason_code": "user_paused",
        "reason_summary": "Paused.",
        "source_kind": "explicit_user_truth",
        "source_ref": "user-authority://pause",
        "evidence_refs": [],
        "current_stage_id": None,
        "current_stage_status": None,
        "current_stage_policy": "no_current_stage_while_inactive",
        "milestone_package_delivered": False,
        "submission_ready": False,
        "package_status": "not_ready",
        "next_action": {
            "surface_kind": "mas_lifecycle_action",
            "action_id": "wait_for_explicit_user_wakeup",
            "action_type": "user_action",
            "owner": "user",
            "status": "paused",
            "summary": "Wait.",
        },
        "resume_policy": {
            "policy_id": "explicit_user_wakeup",
            "auto_resume_allowed": False,
            "explicit_user_wakeup_required": True,
            "allow_stopped_relaunch_required": False,
        },
        "authority_boundary": {
            "truth_owner": "MedAutoScience",
            "domain_truth": True,
            "opl_consumption": "read_only_projection",
            "paper_body_mutated": False,
            "publication_eval_mutated": False,
            "runtime_or_telemetry_can_override": False,
            "submission_package_promoted": False,
        },
    }
    mas_inventory = {
        "surface_kind": "mas_workspace_index",
        "schema_version": "mas.workspace_index.v1",
        "canonical_workspace_root": WORKSPACE_ROOT,
        "recorded_at": "2026-08-01T00:00:00Z",
        "status_counts": {"paused": 1},
        "studies": [
            {
                "study_id": other_id,
                "canonical_study_root": f"studies/{other_id}",
                "display_name": "Other study",
                "status": "paused",
                "business_status": "paused",
                "lifecycle_state": "paused",
                "current_stage_id": None,
                "current_stage_status": None,
                "package_status": "not_ready",
                "lifecycle_ref": "control/lifecycle.json",
                "submission_ready": False,
                "qualification_only": False,
            }
        ],
    }
    workspace_lifecycle = {
        "surface_kind": "workspace_study_lifecycle_control",
        "schema_version": "mas.workspace_study_lifecycle_control.v1",
        "workspace_name": "decoupled_tcm_pilot",
        "recorded_at": "2026-08-01T00:00:00Z",
        "status_counts": {"paused": 1},
        "changed_study_id": other_id,
        "changed_generation": 2,
        "studies": [other_lifecycle],
    }
    request = _request(
        mas_inventory=mas_inventory,
        workspace_lifecycle=workspace_lifecycle,
    )
    result = _handler()(request)

    assert result["status"] == "authorized"
    operations = {
        item["target_relative_path"]: item
        for item in result["opl_host_materialization_request"]["operations"]
    }
    assert operations[MAS_INVENTORY_PATH]["precondition"] == {
        "kind": "existing_exact",
        "sha256": request["current_mas_workspace_index"][
            "mas_workspace_index_sha256"
        ],
        "byte_size": request["current_mas_workspace_index"][
            "mas_workspace_index_byte_size"
        ],
    }
    after = _operation_payload(result, MAS_INVENTORY_PATH)
    assert after["studies"][0] == mas_inventory["studies"][0]
    assert [item["study_id"] for item in after["studies"]] == [
        other_id,
        STUDY_ID,
    ]
    assert after["status_counts"] == {
        "paused": 1,
        "delivered_paused": 1,
    }
    assert all(path != "workspace_index.json" for path in operations)


def test_topology_or_domain_inventory_identity_conflict_fails_closed() -> None:
    missing_topology = _request()
    topology = missing_topology["adoption_authority"][
        "current_opl_topology_inventory"
    ]
    topology["record"]["projects"] = []
    raw = _json_bytes(
        topology["record"]
    )
    topology["topology_bytes_base64"] = base64.b64encode(raw).decode("ascii")
    topology["topology_byte_size"] = len(raw)
    topology["topology_sha256"] = (
        f"sha256:{hashlib.sha256(raw).hexdigest()}"
    )
    result = _handler()(missing_topology)
    assert result["status"] == "typed_blocker"
    assert result["typed_blocker"]["reason_code"] == (
        "existing_study_missing_from_opl_topology"
    )
    assert result["opl_host_materialization_request"] is None

    collision_inventory = {
        "surface_kind": "mas_workspace_index",
        "schema_version": "mas.workspace_index.v1",
        "canonical_workspace_root": WORKSPACE_ROOT,
        "recorded_at": "2026-08-01T00:00:00Z",
        "status_counts": {"delivered_paused": 1},
        "studies": [
            {
                "study_id": STUDY_ID,
                "canonical_study_root": f"studies/{STUDY_ID}",
                "display_name": "Already adopted",
                "status": "delivered_paused",
                "current_stage_id": None,
                "current_stage_status": None,
                "package_status": "milestone_delivered",
                "lifecycle_ref": "control/lifecycle.json",
            }
        ],
    }
    collision = _handler()(_request(mas_inventory=collision_inventory))
    assert collision["status"] == "typed_blocker"
    assert collision["typed_blocker"]["reason_code"] == (
        "existing_study_already_adopted"
    )
    assert collision["opl_host_materialization_request"] is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("owner_receipt", True),
        ("record_owner", "one-person-lab"),
        ("source_owner", "one-person-lab"),
    ],
)
def test_user_authority_exact_bytes_cannot_be_forged(
    field: str, value: object
) -> None:
    request = _request()
    request["adoption_authority"]["user_authority"]["record"][field] = value
    result = _handler()(request)
    assert result["status"] == "invalid_host_input"
    assert result["opl_host_materialization_request"] is None


def test_handler_source_has_no_filesystem_network_or_process_io() -> None:
    source_path = (
        ROOT
        / "src/med_autoscience/authority_handlers/existing_study_adoption.py"
    )
    source = source_path.read_text(encoding="utf-8")
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
