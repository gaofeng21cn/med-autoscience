from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from med_autoscience.authority_handlers.paper_mission import (
    evaluate_paper_mission_authority,
)


ROOT = Path(__file__).resolve().parents[1]


def _evaluate(request: dict[str, Any]) -> dict[str, Any]:
    return evaluate_paper_mission_authority(request)


def _output_validator() -> Draft202012Validator:
    schema = json.loads(
        (
            ROOT / "contracts/schemas/v2/mas-paper-mission-authority.output.schema.json"
        ).read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _schema_validator(filename: str) -> Draft202012Validator:
    schema_dir = ROOT / "contracts/schemas/v2"
    schemas = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in schema_dir.glob("mas-*.schema.json")
    ]
    registry = Registry().with_resources(
        (schema["$id"], Resource.from_contents(schema)) for schema in schemas
    )
    schema = next(item for item in schemas if item["$id"].endswith(f"/{filename}"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, registry=registry)


def test_exact_current_reviews_return_deterministic_owner_receipt(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request()
    original = deepcopy(request)

    first = _evaluate(request)
    second = _evaluate(request)

    assert request == original
    assert first == second
    assert first["status"] == "owner_receipt"
    assert first["stage_outcome"] == {
        "kind": "completed",
        "stage_transition_allowed": True,
        "selects_next_stage": False,
        "publication_or_submission_ready": False,
    }
    receipt = first["owner_receipt"]
    assert receipt["owner"] == "MedAutoScience"
    assert receipt["authorizes_stage_domain_completion"] is True
    assert receipt["authorizes_publication_or_submission"] is False
    assert (
        receipt["generation_identity"]["generation_manifest_ref"]
        == request["generation_manifest_ref"]
    )
    assert (
        receipt["accepted_candidate_admissions"][0]["claim_scope"]
        == request["candidate_admissions"][0]["receipt"]["claim_scope"]
    )
    assert len(receipt["independent_review_receipt_refs"]) == 4


def test_candidate_receipt_inventory_verdict_and_constraints_fail_closed(
    authority_records: Any,
) -> None:
    missing_embedded_receipt = authority_records.paper_request()
    missing_embedded_receipt["candidate_admissions"] = []
    result = _evaluate(missing_embedded_receipt)
    assert result["status"] == "route_back"
    assert result["route_back"]["reason_code"] == (
        "candidate_admission_receipt_required"
    )

    rejected = authority_records.paper_request(candidate_verdict="rejected")
    result = _evaluate(rejected)
    assert result["status"] == "route_back"
    assert result["owner_receipt"] is None
    assert result["route_back"]["reason_code"] == (
        "candidate_admission_receipt_required"
    )

    widened_scope = authority_records.paper_request()
    widened_scope["candidate_admissions"][0]["receipt"]["claim_scope"][
        "permitted_sections"
    ].append("abstract")
    result = _evaluate(widened_scope)
    assert result["status"] == "invalid_host_input"
    assert "canonical receipt" in result["error"]["detail"]

    sensitivity = authority_records.paper_request(candidate_sensitivity_only=True)
    result = _evaluate(sensitivity)
    assert result["status"] == "owner_receipt"
    accepted_scope = result["owner_receipt"]["accepted_candidate_admissions"][0][
        "claim_scope"
    ]
    assert accepted_scope["sensitivity_only"] is True
    assert accepted_scope["abstract_headline_allowed"] is False


def test_review_receipt_requires_mas_issuer_role_verdict_and_independence(
    authority_records: Any,
) -> None:
    forged_issuer = authority_records.paper_request()
    forged_issuer["generation_manifest"]["independent_review_receipts"][0]["receipt"][
        "issuer"
    ] = "OMA"
    result = _evaluate(forged_issuer)
    assert result["status"] == "invalid_host_input"
    assert "issuer must be MedAutoScience" in result["error"]["detail"]

    forged_medical_role = authority_records.paper_request()
    forged_medical_role["generation_manifest"]["independent_review_receipts"][0][
        "receipt"
    ]["authority_role"] = "mas_independent_reference_reviewer"
    result = _evaluate(forged_medical_role)
    assert result["status"] == "invalid_host_input"
    assert "authority_role must be" in result["error"]["detail"]

    forged_verdict = authority_records.paper_request(
        review_verdicts={"medical": "revision_required"}
    )
    wrapper = next(
        item
        for item in forged_verdict["generation_manifest"]["independent_review_receipts"]
        if item["receipt"]["review_lane"] == "medical"
    )
    wrapper["receipt"]["verdict"] = "passed"
    wrapper["receipt"]["defect_refs"] = []
    authority_records.reseal_review_wrapper(wrapper)
    result = _evaluate(forged_verdict)
    assert result["status"] == "route_back"
    assert result["route_back"]["reason_code"] == (
        "independent_review_receipt_not_current"
    )

    producer_as_reviewer = authority_records.paper_request()
    wrapper = producer_as_reviewer["generation_manifest"][
        "independent_review_receipts"
    ][0]
    wrapper["receipt"]["reviewer_attempt_ref"] = deepcopy(
        producer_as_reviewer["host_context"]["producer_attempt_ref"]
    )
    authority_records.reseal_review_wrapper(wrapper)
    result = _evaluate(producer_as_reviewer)
    assert result["status"] == "invalid_host_input"
    assert "reviewer attempt must differ" in result["error"]["detail"]

    duplicate_reviewer = authority_records.paper_request()
    wrappers = duplicate_reviewer["generation_manifest"]["independent_review_receipts"]
    wrappers[1]["receipt"]["reviewer_attempt_ref"] = deepcopy(
        wrappers[0]["receipt"]["reviewer_attempt_ref"]
    )
    authority_records.reseal_review_wrapper(wrappers[1])
    result = _evaluate(duplicate_reviewer)
    assert result["status"] == "invalid_host_input"
    assert "separate reviewer attempts" in result["error"]["detail"]


def test_stale_review_bytes_and_metadata_only_rewrite_cannot_be_reused(
    authority_records: Any,
) -> None:
    stale = authority_records.paper_request()
    table = next(
        item
        for item in stale["generation_manifest"]["artifacts"]
        if item["role"] == "table_file"
    )
    table["sha256"] = authority_records.digest("changed-table-bytes")
    authority_records.refresh_paper_manifest_identity(stale)
    result = _evaluate(stale)
    assert result["status"] == "invalid_host_input"
    assert "generation_manifest_sha256 is stale" in result["error"]["detail"]

    metadata_rewrite = authority_records.paper_request()
    table = next(
        item
        for item in metadata_rewrite["generation_manifest"]["artifacts"]
        if item["role"] == "table_file"
    )
    table["sha256"] = authority_records.digest("second-changed-table-bytes")
    authority_records.refresh_paper_manifest_identity(metadata_rewrite)
    manifest = metadata_rewrite["generation_manifest"]
    for wrapper in manifest["independent_review_receipts"]:
        wrapper["receipt"]["generation_manifest_sha256"] = manifest[
            "generation_manifest_sha256"
        ]
        wrapper["receipt"]["reviewed_members"] = deepcopy(manifest["artifacts"])
        # Deliberately retain the old wrapper ref/hash to model metadata-only reuse.
    result = _evaluate(metadata_rewrite)
    assert result["status"] == "invalid_host_input"
    assert "identity/size/hash" in result["error"]["detail"]


def test_superseded_review_request_replay_routes_back_but_current_retry_passes(
    authority_records: Any,
) -> None:
    current = authority_records.paper_request(
        supplied_review_request_name="review-request-current"
    )
    assert _evaluate(current) == _evaluate(current)
    assert _evaluate(current)["status"] == "owner_receipt"

    old = authority_records.paper_request(
        supplied_review_request_name="review-request-old",
        current_review_request_name="review-request-current",
        superseded_review_request_names=("review-request-old",),
    )
    result = _evaluate(old)
    assert result["status"] == "route_back"
    assert result["route_back"]["reason_code"] == "review_request_authority_stale"
    assert result["stage_outcome"]["stage_transition_allowed"] is False


def test_finalize_requires_publication_generation_six_lanes_and_package_roles(
    authority_records: Any,
) -> None:
    weak_scope = authority_records.paper_request(
        scope="manuscript_generation",
        stage_id="finalize_and_publication_handoff",
    )
    result = _evaluate(weak_scope)
    assert result["status"] == "invalid_host_input"
    assert "requires at least publication_generation" in result["error"]["detail"]

    publication = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
    )
    result = _evaluate(publication)
    assert result["status"] == "owner_receipt"
    lanes = {
        wrapper["receipt"]["review_lane"]
        for wrapper in publication["generation_manifest"]["independent_review_receipts"]
    }
    assert lanes == {
        "medical",
        "statistical",
        "reference",
        "display",
        "publication",
        "exact_byte_package",
    }
    roles = {item["role"] for item in publication["generation_manifest"]["artifacts"]}
    assert {
        "docx",
        "pdf",
        "supplementary_output",
        "final_zip_allowlist",
        "final_zip_member",
        "submission_status",
        "publication_evaluation",
        "next_action_envelope",
        "submission_projection_manifest",
    } <= roles
    transport = result["owner_receipt"]["artifact_projection_transport"]
    assert transport["transport_action_id"] == (
        "opl_pack_materialize_artifact_projection"
    )
    assert transport["generation_id"] == publication["generation_manifest"][
        "generation_id"
    ]
    assert transport["generation_manifest_ref"] == publication[
        "generation_manifest_ref"
    ]
    assert transport["projection_manifest_ref"]["role"] == (
        "submission_projection_manifest"
    )
    assert [
        item["role"] for item in transport["generation_bound_truth_members"]
    ] == [
        "submission_status",
        "publication_evaluation",
        "next_action_envelope",
    ]
    assert transport["completion_marker_paths"] == [
        "STATUS.json",
        "audit/submission_manifest.json",
    ]
    assert transport["opl_request_domain_authorization"] == {
        "owner": "MedAutoScience",
        "ref_source": "owner_receipt.receipt_id",
        "scope": "artifact_projection_only",
        "artifact_body_write_authorized": True,
        "authorizes_quality_publication_or_submission": False,
    }
    assert transport["transport_can_write_domain_truth"] is False

    manuscript = authority_records.paper_request()
    manuscript_result = _evaluate(manuscript)
    assert "artifact_projection_transport" not in manuscript_result["owner_receipt"]

    missing_package_review = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
    )
    missing_package_review["generation_manifest"]["independent_review_receipts"] = [
        wrapper
        for wrapper in missing_package_review["generation_manifest"][
            "independent_review_receipts"
        ]
        if wrapper["receipt"]["review_lane"] != "exact_byte_package"
    ]
    result = _evaluate(missing_package_review)
    assert result["status"] == "route_back"
    assert result["route_back"]["reason_code"] == (
        "independent_reviewer_record_required"
    )

    missing_pdf = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
    )
    missing_pdf["generation_manifest"]["artifacts"] = [
        item
        for item in missing_pdf["generation_manifest"]["artifacts"]
        if item["role"] != "pdf"
    ]
    result = _evaluate(missing_pdf)
    assert result["status"] == "invalid_host_input"
    assert "missing required roles: pdf" in result["error"]["detail"]

    for required_role in (
        "submission_status",
        "publication_evaluation",
        "next_action_envelope",
        "submission_projection_manifest",
    ):
        missing_truth = authority_records.paper_request(
            scope="publication_generation",
            stage_id="finalize_and_publication_handoff",
        )
        missing_truth["generation_manifest"]["artifacts"] = [
            item
            for item in missing_truth["generation_manifest"]["artifacts"]
            if item["role"] != required_role
        ]
        result = _evaluate(missing_truth)
        assert result["status"] == "invalid_host_input"
        assert f"missing required roles: {required_role}" in result["error"][
            "detail"
        ]


def test_finalize_rejects_duplicate_generation_truth_members(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
    )
    status = next(
        item
        for item in request["generation_manifest"]["artifacts"]
        if item["role"] == "submission_status"
    )
    request["generation_manifest"]["artifacts"].append(
        {
            **status,
            "ref": "workspace://study/publication_generation/second-status",
            "sha256": authority_records.digest("second-status-bytes"),
        }
    )
    result = _evaluate(request)

    assert result["status"] == "invalid_host_input"
    assert "requires exactly one submission_status" in result["error"]["detail"]


def test_source_gap_output_debt_and_repair_budget_preserve_stage_semantics(
    authority_records: Any,
) -> None:
    source_gap = authority_records.paper_request()
    source_gap["medical_evidence"]["source_readiness_status"] = "unknown"
    source_gap["medical_evidence"]["source_readiness_receipt_ref"] = None
    result = _evaluate(source_gap)
    assert result["status"] == "route_back"
    assert result["route_back"]["reason_code"] == "source_readiness_record_required"

    no_output = authority_records.paper_request()
    no_output["host_context"]["output_state"] = "no_output"
    result = _evaluate(no_output)
    assert result["status"] == "completed_with_quality_debt"
    assert result["stage_outcome"]["stage_transition_allowed"] is True

    finalize_no_output = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
    )
    finalize_no_output["host_context"]["output_state"] = "no_output"
    result = _evaluate(finalize_no_output)
    assert result["status"] == "route_back"
    assert result["stage_outcome"]["stage_transition_allowed"] is False

    exhausted = authority_records.paper_request(
        review_verdicts={"medical": "revision_required"}
    )
    exhausted["repair_state"] = {
        "status": "exhausted",
        "attempts_used": 3,
        "max_attempts": 3,
        "repair_attempt_refs": [
            authority_records.typed_ref("opl_stage_attempt", f"repair-{index}")
            for index in range(3)
        ],
        "latest_repair_output_ref": authority_records.typed_ref(
            "opl_action_output", "repair-output"
        ),
    }
    result = _evaluate(exhausted)
    assert result["status"] == "completed_with_quality_debt"
    assert "repair_budget_exhausted" in result["quality_debt"]["reason_codes"]


def test_only_typed_hard_or_human_gate_stops_transition(
    authority_records: Any,
) -> None:
    typed = authority_records.paper_request()
    typed["hard_gate"] = {
        "kind": "medical_safety",
        "reason_code": "adverse_event_identity_unresolved",
        "evidence_refs": [
            authority_records.typed_ref("mas_gate_evidence", "medical-safety")
        ],
        "next_owner": "medical_safety_owner",
        "resume_condition": "resolve the adverse-event identity conflict",
    }
    result = _evaluate(typed)
    assert result["status"] == "typed_blocker"
    assert result["typed_blocker"]["blocks_stage_transition"] is True

    human = authority_records.paper_request()
    human["hard_gate"] = {
        "kind": "human_decision",
        "reason_code": "journal_scope_choice_required",
        "evidence_refs": [
            authority_records.typed_ref("mas_gate_evidence", "journal-options")
        ],
        "next_owner": "human_principal_investigator",
        "resume_condition": "select the publication scope",
    }
    result = _evaluate(human)
    assert result["status"] == "human_gate"
    assert result["human_gate"]["blocks_stage_transition"] is True


def test_paper_output_oneof_rejects_contradictory_status_and_receipts(
    authority_records: Any,
) -> None:
    validator = _output_validator()
    owner = _evaluate(authority_records.paper_request())

    route_request = authority_records.paper_request()
    route_request["medical_evidence"]["source_readiness_status"] = "unknown"
    route_request["medical_evidence"]["source_readiness_receipt_ref"] = None
    route = _evaluate(route_request)

    debt_request = authority_records.paper_request()
    debt_request["host_context"]["output_state"] = "no_output"
    debt = _evaluate(debt_request)

    blocker_request = authority_records.paper_request()
    blocker_request["hard_gate"] = {
        "kind": "source_identity",
        "reason_code": "source_identity_conflict",
        "evidence_refs": [
            authority_records.typed_ref("mas_gate_evidence", "source-identity")
        ],
        "next_owner": "source_owner",
        "resume_condition": "resolve source identity",
    }
    blocker = _evaluate(blocker_request)

    human_request = authority_records.paper_request()
    human_request["hard_gate"] = {
        "kind": "human_decision",
        "reason_code": "scope_decision_required",
        "evidence_refs": [
            authority_records.typed_ref("mas_gate_evidence", "scope-decision")
        ],
        "next_owner": "human_principal_investigator",
        "resume_condition": "select the claim scope",
    }
    human = _evaluate(human_request)
    invalid = _evaluate({})

    for result in (owner, route, debt, blocker, human, invalid):
        validator.validate(result)

    contradictory = deepcopy(owner)
    contradictory["status"] = "route_back"
    assert list(validator.iter_errors(contradictory))

    incomplete_blocker = deepcopy(blocker)
    incomplete_blocker["typed_blocker"]["evidence_refs"] = []
    assert list(validator.iter_errors(incomplete_blocker))

    finalize = _evaluate(
        authority_records.paper_request(
            scope="publication_generation",
            stage_id="finalize_and_publication_handoff",
        )
    )
    missing_transport = deepcopy(finalize)
    del missing_transport["owner_receipt"]["artifact_projection_transport"]
    assert list(validator.iter_errors(missing_transport))

    widened_transport = deepcopy(finalize)
    widened_transport["owner_receipt"]["artifact_projection_transport"][
        "opl_request_domain_authorization"
    ]["authorizes_quality_publication_or_submission"] = True
    assert list(validator.iter_errors(widened_transport))


def test_draft202012_input_schemas_accept_exact_records_and_reject_old_abi(
    authority_records: Any,
) -> None:
    candidate_validator = _schema_validator(
        "mas-candidate-admission-authority.input.schema.json"
    )
    paper_validator = _schema_validator("mas-paper-mission-authority.input.schema.json")

    candidate = authority_records.candidate_request()
    candidate_validator.validate(candidate)
    paper_validator.validate(authority_records.paper_request())
    paper_validator.validate(
        authority_records.paper_request(
            scope="publication_generation",
            stage_id="finalize_and_publication_handoff",
        )
    )

    old_candidate_abi = deepcopy(candidate)
    old_candidate_abi["candidate"]["proposed_disposition"] = "accepted"
    assert list(candidate_validator.iter_errors(old_candidate_abi))

    old_paper_abi = authority_records.paper_request()
    old_paper_abi["independent_review"] = {
        "status": "passed",
    }
    assert list(paper_validator.iter_errors(old_paper_abi))


def test_registry_catalog_schemas_and_audit_bind_exact_handlers() -> None:
    registry = json.loads(
        (ROOT / "contracts/domain_handler_registry.json").read_text(encoding="utf-8")
    )
    catalog = json.loads(
        (ROOT / "contracts/action_catalog.json").read_text(encoding="utf-8")
    )
    audit = json.loads(
        (ROOT / "contracts/functional_privatization_audit.json").read_text(
            encoding="utf-8"
        )
    )
    input_schema = json.loads(
        (
            ROOT / "contracts/schemas/v2/mas-paper-mission-authority.input.schema.json"
        ).read_text(encoding="utf-8")
    )
    output_schema = json.loads(
        (
            ROOT / "contracts/schemas/v2/mas-paper-mission-authority.output.schema.json"
        ).read_text(encoding="utf-8")
    )

    paper_handler = next(
        item
        for item in registry["handlers"]
        if item["handler_id"] == "mas.paper-mission-authority-evaluate"
    )
    assert paper_handler["binding"] == {
        "kind": "python_callable",
        "module": "med_autoscience.authority_handlers.paper_mission",
        "callable": "evaluate_paper_mission_authority",
    }
    action = next(
        item
        for item in catalog["actions"]
        if item["action_id"] == "paper_mission_authority_evaluate"
    )
    assert action["required_fields"] == input_schema["required"]
    assert input_schema["additionalProperties"] is False
    assert input_schema["properties"]["schema_version"] == {"const": 2}
    assert input_schema["properties"]["generation_manifest"] == {
        "$ref": "mas-evidence-generation-manifest.schema.json"
    }
    assert len(output_schema["oneOf"]) == 6
    assert [module["module_id"] for module in audit["modules"]] == [
        "mas.paper_mission_authority",
        "mas.candidate_admission_authority",
        "mas.agent_lab_self_evolution_closeout",
    ]
