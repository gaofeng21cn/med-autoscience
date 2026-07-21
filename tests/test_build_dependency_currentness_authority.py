from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from med_autoscience.authority_handlers.build_dependency_currentness import (
    evaluate_build_dependency_currentness_authority,
)
from med_autoscience.authority_handlers.paper_mission import (
    evaluate_paper_mission_authority,
)


ROOT = Path(__file__).resolve().parents[1]


def _validator(name: str) -> Draft202012Validator:
    schema = json.loads(
        (ROOT / "contracts" / "schemas" / "v2" / name).read_text(encoding="utf-8")
    )
    return Draft202012Validator(schema)


def test_managed_authority_handler_issues_exact_owner_result(
    authority_records: Any,
) -> None:
    paper = authority_records.paper_request()
    dependency_ref = paper["generation_manifest"]["selected_build_binding"][
        "dependency_manifest_ref"
    ]
    request = authority_records.build_dependency_currentness_authority_request(
        dependency_ref, "current"
    )

    first = evaluate_build_dependency_currentness_authority(request)
    second = evaluate_build_dependency_currentness_authority(request)

    assert first == second
    assert first["status"] == "owner_authority"
    assert first["authority_record"]["issuer_attempt_ref"] == request[
        "authority_context"
    ]["managed_authority_attempt_ref"]
    assert first["authority_record"]["managed_authority_attempt_receipt_ref"] == (
        request["authority_context"]["managed_authority_attempt_receipt_ref"]
    )
    assert first["authority_record"]["owner_ledger_ref"] == request[
        "authority_context"
    ]["owner_ledger_ref"]
    assert first["authority_record"]["reviewer_response_currentness"][
        "owner_ledger_history_ref"
    ] == request["authority_context"]["owner_ledger_ref"]
    assert first["opl_injection_provenance"]["owner_ledger_history_ref"] == request[
        "authority_context"
    ]["owner_ledger_ref"]
    assert first["authority_record"]["authority_boundary"] == {
        "authorizes_publication": False,
        "authorizes_submission": False,
    }
    _validator(
        "mas-build-dependency-currentness-authority.input.schema.json"
    ).validate(request)
    _validator(
        "mas-build-dependency-currentness-authority.output.schema.json"
    ).validate(first)


def test_managed_authority_attempt_must_differ_from_generation_producer(
    authority_records: Any,
) -> None:
    paper = authority_records.paper_request()
    dependency_ref = paper["generation_manifest"]["selected_build_binding"][
        "dependency_manifest_ref"
    ]
    request = authority_records.build_dependency_currentness_authority_request(
        dependency_ref, "current"
    )
    request["authority_context"]["managed_authority_attempt_ref"] = deepcopy(
        request["authority_context"]["generation_producer_attempt_ref"]
    )

    result = evaluate_build_dependency_currentness_authority(request)

    assert result["status"] == "invalid_host_input"
    assert "must differ from generation producer attempt" in result["error"]["detail"]
    _validator(
        "mas-build-dependency-currentness-authority.output.schema.json"
    ).validate(result)


def test_reviewer_response_history_cannot_introduce_parallel_owner_ledger(
    authority_records: Any,
) -> None:
    paper = authority_records.paper_request()
    dependency_ref = paper["generation_manifest"]["selected_build_binding"][
        "dependency_manifest_ref"
    ]
    request = authority_records.build_dependency_currentness_authority_request(
        dependency_ref, "current"
    )
    request["reviewer_response_currentness"][
        "owner_ledger_history_ref"
    ] = authority_records.exact_ref("opl_action_output", "parallel-history-ledger")

    result = evaluate_build_dependency_currentness_authority(request)

    assert result["status"] == "invalid_host_input"
    assert "must reuse the managed build-currentness owner ledger" in result[
        "error"
    ]["detail"]


def test_frozen_reviewer_response_history_requires_original_bytes_or_new_revision(
    authority_records: Any,
) -> None:
    frozen = authority_records.paper_request(
        reviewer_response_candidate_state="frozen",
        reviewer_response_post_freeze_disposition="external_synthesis_bound",
    )
    dependency_ref = frozen["generation_manifest"]["selected_build_binding"][
        "dependency_manifest_ref"
    ]
    currentness = deepcopy(
        frozen["selected_build_currentness_authority"]["authority_record"][
            "reviewer_response_currentness"
        ]
    )
    original_response_ref = deepcopy(currentness["response_ref"])

    accepted = evaluate_build_dependency_currentness_authority(
        authority_records.build_dependency_currentness_authority_request(
            dependency_ref, "current", currentness
        )
    )
    assert accepted["status"] == "owner_authority"
    assert accepted["authority_record"]["reviewer_response_currentness"][
        "prior_frozen_response_ref"
    ] == original_response_ref

    replaced_without_revision = deepcopy(currentness)
    replaced_without_revision["response_ref"] = authority_records.exact_ref(
        "mas_artifact", "same-generation-replaced-response"
    )
    rejected = evaluate_build_dependency_currentness_authority(
        authority_records.build_dependency_currentness_authority_request(
            dependency_ref, "current", replaced_without_revision
        )
    )
    assert rejected["status"] == "invalid_host_input"
    assert "same frozen generation cannot replace reviewer response bytes" in rejected[
        "error"
    ]["detail"]

    new_revision = authority_records.paper_request(
        reviewer_response_candidate_state="frozen",
        reviewer_response_post_freeze_disposition=(
            "scientific_change_requires_new_revision"
        ),
    )
    new_revision_currentness = deepcopy(
        new_revision["selected_build_currentness_authority"]["authority_record"][
            "reviewer_response_currentness"
        ]
    )
    new_revision_currentness["response_ref"] = authority_records.exact_ref(
        "mas_artifact", "new-revision-response"
    )
    admitted_revision = evaluate_build_dependency_currentness_authority(
        authority_records.build_dependency_currentness_authority_request(
            new_revision["generation_manifest"]["selected_build_binding"][
                "dependency_manifest_ref"
            ],
            "current",
            new_revision_currentness,
        )
    )
    assert admitted_revision["status"] == "owner_authority"
    assert admitted_revision["authority_record"]["reviewer_response_currentness"][
        "new_revision_ref"
    ] is not None


def test_input_schema_and_handler_reject_non_opl_provenance_ref_kinds(
    authority_records: Any,
) -> None:
    paper = authority_records.paper_request()
    dependency_ref = paper["generation_manifest"]["selected_build_binding"][
        "dependency_manifest_ref"
    ]
    request = authority_records.build_dependency_currentness_authority_request(
        dependency_ref, "current"
    )
    validator = _validator(
        "mas-build-dependency-currentness-authority.input.schema.json"
    )

    for field in (
        "managed_authority_attempt_receipt_ref",
        "owner_ledger_ref",
    ):
        tampered = deepcopy(request)
        tampered["authority_context"][field]["kind"] = "mas_artifact"

        assert not validator.is_valid(tampered)
        assert evaluate_build_dependency_currentness_authority(tampered)[
            "status"
        ] == "invalid_host_input"


def test_output_schema_rejects_empty_objects_and_canonical_field_tampering(
    authority_records: Any,
) -> None:
    paper = authority_records.paper_request()
    dependency_ref = paper["generation_manifest"]["selected_build_binding"][
        "dependency_manifest_ref"
    ]
    request = authority_records.build_dependency_currentness_authority_request(
        dependency_ref, "current"
    )
    result = evaluate_build_dependency_currentness_authority(request)
    validator = _validator(
        "mas-build-dependency-currentness-authority.output.schema.json"
    )

    validator.validate(result)
    for field in (
        "authority_ref",
        "authority_record",
        "opl_injection_provenance",
    ):
        empty_object = deepcopy(result)
        empty_object[field] = {}
        assert not validator.is_valid(empty_object)

    tampered_ref = deepcopy(result)
    tampered_ref["authority_ref"]["kind"] = "mas_artifact"
    assert not validator.is_valid(tampered_ref)

    tampered_boundary = deepcopy(result)
    tampered_boundary["authority_record"]["authority_boundary"][
        "authorizes_publication"
    ] = True
    assert not validator.is_valid(tampered_boundary)

    tampered_provenance = deepcopy(result)
    tampered_provenance["opl_injection_provenance"][
        "host_context_authority_ref_field"
    ] = "forged_authority_ref"
    assert not validator.is_valid(tampered_provenance)


def test_owner_handler_output_round_trips_through_host_bound_paper_mission(
    authority_records: Any,
) -> None:
    paper = authority_records.paper_request()
    dependency_ref = paper["generation_manifest"]["selected_build_binding"][
        "dependency_manifest_ref"
    ]
    authority_request = (
        authority_records.build_dependency_currentness_authority_request(
            dependency_ref,
            "current",
            paper["selected_build_currentness_authority"]["authority_record"][
                "reviewer_response_currentness"
            ],
        )
    )
    authority_result = evaluate_build_dependency_currentness_authority(
        authority_request
    )

    assert paper["selected_build_currentness_authority"] == {
        "authority_ref": authority_result["authority_ref"],
        "authority_record": authority_result["authority_record"],
    }
    assert paper["host_context"][
        "build_dependency_currentness_authority_ref"
    ] == authority_result["authority_ref"]
    assert paper["host_context"][
        "build_dependency_currentness_authority_issuer_attempt_ref"
    ] == authority_result["authority_record"]["issuer_attempt_ref"]
    result = evaluate_paper_mission_authority(paper)
    assert result["status"] == "owner_receipt"
    assert result["owner_receipt"][
        "selected_build_currentness_authority_ref"
    ] == authority_result["authority_ref"]


def test_registry_action_declares_managed_attempt_integration_dependency() -> None:
    registry = json.loads(
        (ROOT / "contracts/domain_handler_registry.json").read_text(encoding="utf-8")
    )
    catalog = json.loads(
        (ROOT / "contracts/action_catalog.json").read_text(encoding="utf-8")
    )
    handler = next(
        item
        for item in registry["handlers"]
        if item["handler_id"]
        == "mas.build-dependency-currentness-authority-evaluate"
    )
    assert handler["binding"] == {
        "kind": "python_callable",
        "module": "med_autoscience.authority_handlers.build_dependency_currentness",
        "callable": "evaluate_build_dependency_currentness_authority",
    }
    action = next(
        item
        for item in catalog["actions"]
        if item["action_id"] == "build_dependency_currentness_authority_evaluate"
    )
    assert action["execution_binding"]["handler_ref"] == (
        "handler:mas.build-dependency-currentness-authority-evaluate"
    )
    provenance = action["managed_authority_provenance_dependency"]
    assert provenance["requires_distinct_managed_authority_attempt"] is True
    assert provenance["opl_must_persist_owner_result_before_paper_mission_injection"] is True
    assert provenance["runtime_integration_status"] == "declared_not_current"
