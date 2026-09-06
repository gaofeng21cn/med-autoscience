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

from med_autoscience.authority_handlers.study_initialization import (
    ACTION_ID,
    evaluate_study_initialization_authority,
)
from med_autoscience.authority_handlers.study_lifecycle_reactivation_parts.request import (
    _normalize_lifecycle_record,
)


ROOT = Path(__file__).resolve().parents[1]
STUDY_ID = "first-study"


def _bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _bind(request: dict[str, Any], raw: bytes | None = None) -> None:
    inventory = request["current_inventory"]
    raw = raw if raw is not None else _bytes(inventory["record"])
    inventory.update(
        inventory_bytes_base64=base64.b64encode(raw).decode(),
        inventory_byte_size=len(raw),
        inventory_sha256=_digest(raw),
    )


def _request() -> dict[str, Any]:
    request = {
        "authority_context": {
            "action_id": ACTION_ID,
            "handler_call_ref": "opl://standard-agent-action-run/initialization-test",
            "owner_ledger_ref": "file:///workspace/control/opl/owner-ledger.json",
            "original_admission_request_ref": "file:///workspace/control/opl/original.json",
            "original_admission_request_sha256": _digest(b"original"),
            "admission_scope_id": f"lifecycle-initialization:{_digest(b'scope')}",
            "requested_action_id": "direction_and_route_selection",
            "requested_run_id": "first-stage-run",
            "original_invocation_sha256": _digest(b"invocation"),
            "requested_at": "2026-09-06T03:00:00Z",
        },
        "work_item_identity": {
            "work_item_id": STUDY_ID,
            "canonical_workspace_root": "/workspace",
            "canonical_work_item_root": f"studies/{STUDY_ID}",
            "work_item_root_ref": f"file:///workspace/studies/{STUDY_ID}",
            "descriptor_domain_id": "medautoscience",
        },
        "current_inventory": {
            "inventory_ref": "workspace_index.json",
            "record": {
                "surface_kind": "opl_workspace_index",
                "version": "workspace-index.v1",
                "title": "Research workspace",
                "projects": [{"project_id": STUDY_ID}],
                "studies": [
                    {"study_id": "existing", "canonical_study_root": "studies/existing", "status": "paused"},
                    {"study_id": STUDY_ID, "canonical_study_root": f"studies/{STUDY_ID}"},
                ],
            },
            "selected_item_index": 1,
        },
    }
    _bind(request)
    return request


def _schema(name: str) -> dict[str, Any]:
    return json.loads((ROOT / "contracts/schemas/v2" / name).read_text())


def _evaluate(request: dict[str, Any]) -> dict[str, Any]:
    result = evaluate_study_initialization_authority(request)
    Draft202012Validator(_schema("mas-study-initialization-authority.output.schema.json")).validate(result)
    return result


def _replacement(operation: dict[str, Any]) -> dict[str, Any]:
    raw = base64.b64decode(operation["replacement_bytes_base64"])
    assert operation["replacement_sha256"] == _digest(raw)
    assert operation["replacement_byte_size"] == len(raw)
    return json.loads(raw)


def test_initialization_authorizes_exact_three_file_cas_and_preserves_inventory() -> None:
    request = _request()
    original = deepcopy(request)
    Draft202012Validator(_schema("mas-study-initialization-authority.input.schema.json")).validate(request)
    result = _evaluate(request)
    assert result["status"] == "authorized"
    assert request == original
    assert _evaluate(request) == result
    operations = result["opl_host_materialization_request"]["operations"]
    assert len(operations) == 3
    assert operations[0]["precondition"] == {
        "kind": "existing_exact",
        "sha256": request["current_inventory"]["inventory_sha256"],
        "byte_size": request["current_inventory"]["inventory_byte_size"],
    }
    assert [op["precondition"]["kind"] for op in operations] == ["existing_exact", "absent", "absent"]
    inventory, lifecycle, receipt = map(_replacement, operations)
    assert inventory["studies"][0] == original["current_inventory"]["record"]["studies"][0]
    assert inventory["projects"] == original["current_inventory"]["record"]["projects"]
    assert inventory["studies"][1]["lifecycle_ref"] == "control/lifecycle.json"
    assert receipt["lifecycle_ref"] == operations[1]["target_relative_path"]
    assert lifecycle["lifecycle_state"] == "active"
    assert lifecycle["generation"] == 1
    assert _normalize_lifecycle_record(lifecycle) == lifecycle
    assert lifecycle["submission_ready"] is False
    assert lifecycle["package_status"] == "not_ready"
    assert receipt == result["initialization_receipt"]
    assert receipt["stage_body_authorized"] is True
    assert receipt["publication_authorized"] is False
    assert receipt["submission_authorized"] is False
    assert receipt["from_state"] == "uninitialized"
    assert receipt["from_generation"] == 0
    assert receipt["lifecycle_sha256"] == f"sha256:{operations[1]['replacement_sha256']}"
    assert receipt["original_invocation_sha256"] == request["authority_context"]["original_invocation_sha256"]
    assert receipt["admission_scope_id"] == request["authority_context"]["admission_scope_id"]
    assert result["mas_lifecycle_cas_mutation_authorization"]["authority_receipt_ref"] == receipt["receipt_ref"]


@pytest.mark.parametrize("quality", [None, "unknown", "insufficient", "failed", {"verdict": "low", "score": 0}])
def test_unknown_or_low_quality_does_not_block_or_become_a_quality_pass(quality: Any) -> None:
    request = _request()
    request["current_inventory"]["record"]["studies"][1]["quality"] = quality
    _bind(request)
    result = _evaluate(request)
    assert result["status"] == "authorized"
    inventory, lifecycle, receipt = map(_replacement, result["opl_host_materialization_request"]["operations"])
    assert inventory["studies"][1]["quality"] == quality
    assert "quality" not in lifecycle
    assert receipt["quality_verdict_created"] is False
    assert receipt["publication_authorized"] is False
    assert receipt["submission_authorized"] is False


@pytest.mark.parametrize("field,value", [
    ("qualification_only", True), ("lifecycle_ref", None),
    ("lifecycle_state", "paused"), ("status", "stopped"),
    ("generation", 1), ("stage_body_authorized", False),
    ("business_action_authorized", False),
    ("publication_authorized", True), ("submission_ready", True),
])
def test_existing_domain_or_qualification_truth_is_not_promoted(field: str, value: Any) -> None:
    request = _request()
    request["current_inventory"]["record"]["studies"][1][field] = value
    _bind(request)
    result = _evaluate(request)
    assert result["status"] == "typed_blocker"
    assert result["typed_blocker"]["reason_code"] == "study_is_not_uninitialized"
    assert result["opl_host_materialization_request"] is None


@pytest.mark.parametrize("mutation", [
    lambda r: r["current_inventory"].update(inventory_sha256="0" * 64),
    lambda r: r["current_inventory"].update(inventory_byte_size=1),
    lambda r: r["current_inventory"].update(inventory_bytes_base64="not-base64"),
    lambda r: r["current_inventory"].update(selected_item_index=0),
    lambda r: r["current_inventory"].update(selected_item_index=-1),
    lambda r: r["current_inventory"].update(selected_item_index=True),
    lambda r: r["current_inventory"].update(inventory_ref="../workspace_index.json"),
    lambda r: r["current_inventory"]["record"].update(title="unbound change"),
    lambda r: r["work_item_identity"].update(work_item_id="different-study"),
    lambda r: r["work_item_identity"].update(work_item_id=" first-study "),
    lambda r: r["work_item_identity"].update(work_item_root_ref="file:///other/studies/first-study"),
    lambda r: r["work_item_identity"].update(canonical_workspace_root="/workspace/../other"),
    lambda r: r["authority_context"].update(requested_action_id="submit_publication"),
    lambda r: r["authority_context"].update(requested_at="yesterday"),
])
def test_malformed_stale_or_mismatched_input_fails_without_cas(mutation: Any) -> None:
    request = _request()
    mutation(request)
    result = _evaluate(request)
    assert result["status"] == "invalid_host_input"
    assert result["opl_host_materialization_request"] is None


def test_duplicate_identity_is_rejected() -> None:
    request = _request()
    request["current_inventory"]["record"]["studies"].append(deepcopy(request["current_inventory"]["record"]["studies"][1]))
    _bind(request)
    assert _evaluate(request)["status"] == "invalid_host_input"


def test_study_name_does_not_infer_qualification_authority() -> None:
    request = _request()
    study_id = "qualification-research-topic"
    root = f"studies/{study_id}"
    request["work_item_identity"].update(
        work_item_id=study_id, canonical_work_item_root=root,
        work_item_root_ref=f"file:///workspace/{root}",
    )
    request["current_inventory"]["record"]["studies"][1].update(
        study_id=study_id, canonical_study_root=root,
    )
    _bind(request)
    assert _evaluate(request)["status"] == "authorized"


def test_node_file_url_encoding_preserves_canonical_workspace_identity() -> None:
    request = _request()
    request["work_item_identity"].update(
        canonical_workspace_root="/workspace (trial)/\u7814\u7a76",
        work_item_root_ref="file:///workspace%20(trial)/%E7%A0%94%E7%A9%B6/studies/first-study",
    )
    assert _evaluate(request)["status"] == "authorized"


def test_noncanonical_json_whitespace_keeps_original_exact_cas_precondition() -> None:
    request = _request()
    raw = json.dumps(request["current_inventory"]["record"], indent=4).encode() + b"\n"
    _bind(request, raw)
    result = _evaluate(request)
    assert result["status"] == "authorized"
    assert result["opl_host_materialization_request"]["operations"][0]["precondition"]["sha256"] == _digest(raw)


def test_duplicate_json_keys_are_rejected_even_with_matching_digest() -> None:
    request = _request()
    raw = _bytes(request["current_inventory"]["record"]).replace(b'"title":', b'"title":"duplicate","title":')
    _bind(request, raw)
    assert _evaluate(request)["status"] == "invalid_host_input"


def test_new_inventory_snapshot_produces_a_distinct_cas_authorization() -> None:
    first = _request()
    second = deepcopy(first)
    second["current_inventory"]["record"]["studies"][0]["status"] = "active"
    _bind(second)
    first_result, second_result = _evaluate(first), _evaluate(second)
    assert first_result["status"] == second_result["status"] == "authorized"
    assert first_result["mas_lifecycle_cas_mutation_authorization"]["authorization_ref"] != second_result["mas_lifecycle_cas_mutation_authorization"]["authorization_ref"]
    assert first_result["opl_host_materialization_request"]["operations"][0]["precondition"] != second_result["opl_host_materialization_request"]["operations"][0]["precondition"]


def test_catalog_registry_and_all_stage_receipt_bindings_resolve() -> None:
    catalog = json.loads((ROOT / "contracts/action_catalog.json").read_text())
    registry = json.loads((ROOT / "contracts/domain_handler_registry.json").read_text())
    action = next(item for item in catalog["actions"] if item["action_id"] == ACTION_ID)
    handler = next(item for item in registry["handlers"] if f"handler:{item['handler_id']}" == action["execution_binding"]["handler_ref"])
    binding = handler["binding"]
    assert getattr(importlib.import_module(binding["module"]), binding["callable"]) is evaluate_study_initialization_authority
    for stage in catalog["actions"]:
        admission = stage.get("authority_boundary", {}).get("lifecycle_admission_contract")
        if admission is not None:
            assert admission["initialization_action_id"] == ACTION_ID
            assert admission["initialization_request_input_field_map"] == {
                "authority_context": "/authority_context",
                "work_item_identity": "/work_item_identity",
                "current_inventory": "/current_inventory",
            }
    Draft202012Validator(_schema("mas-stage-action.input.schema.json")).validate({
        "workspace_root": "/workspace", "study_id": STUDY_ID,
        "lifecycle_admission": {
            "surface_kind": "opl_domain_lifecycle_admission",
            "version": "opl-domain-lifecycle-admission.v1",
            "mode": "initialization_receipt",
            "domain_authority_result_ref": "file:///workspace/authority.json",
            "domain_authority_result_sha256": f"sha256:{_digest(b'authority')}",
            "materialization_receipt_ref": "file:///opl-state/materialization.json",
            "materialization_receipt_sha256": f"sha256:{_digest(b'cas')}",
        },
    })
