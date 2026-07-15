from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from med_autoscience.authority_handlers.candidate_admission import (
    evaluate_candidate_admission_authority,
)


ROOT = Path(__file__).resolve().parents[1]


def _evaluate(request: dict[str, Any]) -> dict[str, Any]:
    return evaluate_candidate_admission_authority(request)


def _output_validator() -> Draft202012Validator:
    schema = json.loads(
        (
            ROOT
            / "contracts/schemas/v2/mas-candidate-admission-authority.output.schema.json"
        ).read_text(encoding="utf-8")
    )
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def test_current_exact_candidate_retry_returns_deterministic_acceptance(
    authority_records: Any,
) -> None:
    request = authority_records.candidate_request()
    original = deepcopy(request)

    first = _evaluate(request)
    second = _evaluate(request)

    assert request == original
    assert first == second
    assert first["status"] == "accepted"
    receipt = first["disposition_receipt"]
    assert receipt["disposition"] == "accepted"
    assert receipt["authorizes_manuscript_consumption"] is True
    assert receipt["authorizes_publication_or_submission"] is False
    assert receipt["generation_manifest_ref"] == request["generation_manifest_ref"]
    assert (
        receipt["candidate_ref"]["sha256"]
        == request["candidate"]["candidate_member"]["sha256"]
    )
    assert receipt["claim_scope"] == request["candidate"]["claim_scope"]


def test_host_forged_proposal_and_fake_receipt_digest_fail_closed(
    authority_records: Any,
) -> None:
    forged_proposal = authority_records.candidate_request()
    forged_proposal["candidate"]["proposed_disposition"] = "accepted"
    result = _evaluate(forged_proposal)
    assert result["status"] == "invalid_host_input"
    assert "unsupported fields" in result["error"]["detail"]

    canonical_rewrite = authority_records.candidate_request(verdict="rejected")
    rewritten = deepcopy(canonical_rewrite["adjudicator_receipt"])
    rewritten["verdict"] = "accepted"
    rewritten["decision_code"] = "accepted_for_exact_claim_scope"
    core = {
        name: value
        for name, value in rewritten.items()
        if name not in {"receipt_id", "receipt_size_bytes", "receipt_fingerprint"}
    }
    rewritten = authority_records.seal(core, "mas-candidate-adjudicator")
    canonical_rewrite["adjudicator_receipt"] = rewritten
    canonical_rewrite["adjudicator_context"]["adjudicator_receipt_ref"] = (
        authority_records.receipt_ref("mas_candidate_adjudicator_receipt", rewritten)
    )
    result = _evaluate(canonical_rewrite)
    assert result["status"] == "invalid_host_input"
    assert "does not authorize the supplied adjudicator" in result["error"]["detail"]

    fake_artifact_digest = authority_records.candidate_request()
    fake_artifact_digest["candidate"]["candidate_member"]["sha256"] = (
        authority_records.digest("host-forged-candidate-bytes")
    )
    result = _evaluate(fake_artifact_digest)
    assert result["status"] == "invalid_host_input"
    assert "absent from the exact generation manifest" in result["error"]["detail"]

    fake_receipt_digest = authority_records.candidate_request()
    fake_receipt_digest["adjudicator_context"]["adjudicator_receipt_ref"]["sha256"] = (
        authority_records.digest("host-forged-adjudicator-receipt")
    )
    result = _evaluate(fake_receipt_digest)
    assert result["status"] == "invalid_host_input"
    assert "does not authorize the supplied adjudicator" in result["error"]["detail"]


def test_manifest_fingerprint_and_member_proof_reject_mixed_generation(
    authority_records: Any,
) -> None:
    mismatched_manifest = authority_records.candidate_request()
    mismatched_manifest["generation_manifest"]["generation_manifest_sha256"] = (
        authority_records.digest("unrelated-manifest")
    )
    result = _evaluate(mismatched_manifest)
    assert result["status"] == "invalid_host_input"
    assert "does not match canonical members" in result["error"]["detail"]

    old_evidence = authority_records.candidate_request()
    old_evidence["candidate"]["evidence_members"][0]["ref"] = (
        "mas-evidence://prior-generation"
    )
    result = _evaluate(old_evidence)
    assert result["status"] == "invalid_host_input"
    assert "absent from the exact generation manifest" in result["error"]["detail"]

    duplicated_generation_field = authority_records.candidate_request()
    duplicated_generation_field["generation_manifest"]["artifacts"][0][
        "generation_id"
    ] = "prior-generation"
    result = _evaluate(duplicated_generation_field)
    assert result["status"] == "invalid_host_input"
    assert "unsupported fields" in result["error"]["detail"]


def test_superseded_request_replay_blocks_but_current_retry_is_idempotent(
    authority_records: Any,
) -> None:
    current = authority_records.candidate_request(
        request_name="candidate-request-current"
    )
    assert _evaluate(current) == _evaluate(current)
    assert _evaluate(current)["status"] == "accepted"

    stale = authority_records.candidate_request(
        request_name="candidate-request-old",
        current_request_name="candidate-request-current",
        superseded_request_names=("candidate-request-old",),
    )
    result = _evaluate(stale)
    assert result["status"] == "typed_blocker"
    assert result["typed_blocker"]["gate_kind"] == "source_currentness"
    assert result["typed_blocker"]["reason_code"] == (
        "superseded_candidate_admission_request"
    )
    assert result["typed_blocker"]["authorizes_manuscript_consumption"] is False


def test_claim_scope_constraints_are_receipt_bound_and_sensitivity_guarded(
    authority_records: Any,
) -> None:
    widened_scope = authority_records.candidate_request()
    widened_scope["candidate"]["claim_scope"]["permitted_sections"].append("abstract")
    result = _evaluate(widened_scope)
    assert result["status"] == "invalid_host_input"
    assert "adjudicator_receipt is not bound" in result["error"]["detail"]
    assert "claim_scope" in result["error"]["detail"]

    sensitivity_headline = authority_records.candidate_request(
        sensitivity_only=True,
        abstract_headline_allowed=True,
    )
    result = _evaluate(sensitivity_headline)
    assert result["status"] == "invalid_host_input"
    assert "sensitivity-only claim scope" in result["error"]["detail"]


def test_typed_route_and_waiver_reject_free_text_or_incomplete_records(
    authority_records: Any,
) -> None:
    route = authority_records.candidate_request(verdict="route_back")
    result = _evaluate(route)
    assert result["status"] == "route_back"
    assert result["route_back"]["route_code"] == "claim_scope_revision_required"
    assert result["route_back"]["authorizes_manuscript_consumption"] is False

    free_text_route = authority_records.candidate_request(verdict="route_back")
    free_text_route["adjudicator_receipt"]["decision_code"] = "please_revise"
    result = _evaluate(free_text_route)
    assert result["status"] == "invalid_host_input"
    assert "decision_code" in result["error"]["detail"]

    waived = authority_records.candidate_request(verdict="waived")
    result = _evaluate(waived)
    assert result["status"] == "waived"
    assert result["waiver"]["authorizes_manuscript_consumption"] is False

    incomplete_waiver = authority_records.candidate_request(verdict="waived")
    incomplete_waiver["adjudicator_receipt"]["waiver"]["evidence_refs"] = []
    result = _evaluate(incomplete_waiver)
    assert result["status"] == "invalid_host_input"
    assert "evidence_refs must not be empty" in result["error"]["detail"]


def test_candidate_hard_and_human_gates_preserve_authority_boundary(
    authority_records: Any,
) -> None:
    typed = authority_records.candidate_request()
    typed["hard_gate"] = {
        "kind": "source_identity",
        "reason_code": "source_identity_conflict",
        "evidence_refs": [
            authority_records.typed_ref("mas_gate_evidence", "source-identity")
        ],
        "next_owner": "source_owner",
        "resume_condition": "resolve source identity",
    }
    result = _evaluate(typed)
    assert result["status"] == "typed_blocker"
    assert result["typed_blocker"]["authorizes_manuscript_consumption"] is False

    human = authority_records.candidate_request()
    human["hard_gate"] = {
        "kind": "human_decision",
        "reason_code": "clinical_scope_choice_required",
        "evidence_refs": [
            authority_records.typed_ref("mas_gate_evidence", "clinical-scope")
        ],
        "next_owner": "human_principal_investigator",
        "resume_condition": "select the defensible clinical scope",
    }
    result = _evaluate(human)
    assert result["status"] == "human_gate"
    assert result["human_gate"]["authorizes_manuscript_consumption"] is False


def test_candidate_output_oneof_rejects_contradictory_status_receipt(
    authority_records: Any,
) -> None:
    validator = _output_validator()
    accepted = _evaluate(authority_records.candidate_request())
    rejected = _evaluate(authority_records.candidate_request(verdict="rejected"))
    route = _evaluate(authority_records.candidate_request(verdict="route_back"))
    waived = _evaluate(authority_records.candidate_request(verdict="waived"))
    for result in (accepted, rejected, route, waived):
        validator.validate(result)

    contradictory = deepcopy(accepted)
    contradictory["status"] = "rejected"
    assert list(validator.iter_errors(contradictory))

    incomplete_blocker = _evaluate(authority_records.candidate_request())
    incomplete_blocker["status"] = "typed_blocker"
    incomplete_blocker["disposition_receipt"] = None
    incomplete_blocker["typed_blocker"] = {
        "gate_kind": "source_currentness",
        "reason_code": "superseded_candidate_admission_request",
        "evidence_refs": [],
        "next_owner": "mas_generation_currentness_owner",
        "resume_condition": "use the current request",
        "authorizes_manuscript_consumption": False,
        "requires_host_exact_byte_persistence": True,
    }
    assert list(validator.iter_errors(incomplete_blocker))


def test_catalog_registry_and_schemas_bind_exact_candidate_authority() -> None:
    registry = json.loads(
        (ROOT / "contracts/domain_handler_registry.json").read_text(encoding="utf-8")
    )
    catalog = json.loads(
        (ROOT / "contracts/action_catalog.json").read_text(encoding="utf-8")
    )
    input_schema = json.loads(
        (
            ROOT
            / "contracts/schemas/v2/mas-candidate-admission-authority.input.schema.json"
        ).read_text(encoding="utf-8")
    )
    output_schema = json.loads(
        (
            ROOT
            / "contracts/schemas/v2/mas-candidate-admission-authority.output.schema.json"
        ).read_text(encoding="utf-8")
    )

    handler = next(
        item
        for item in registry["handlers"]
        if item["handler_id"] == "mas.candidate-admission-authority-evaluate"
    )
    assert handler["binding"] == {
        "kind": "python_callable",
        "module": "med_autoscience.authority_handlers.candidate_admission",
        "callable": "evaluate_candidate_admission_authority",
    }
    action = next(
        item
        for item in catalog["actions"]
        if item["action_id"] == "candidate_admission_authority_evaluate"
    )
    assert action["execution_binding"]["handler_ref"] == (
        "handler:mas.candidate-admission-authority-evaluate"
    )
    assert action["required_fields"] == input_schema["required"]
    assert input_schema["additionalProperties"] is False
    assert len(output_schema["oneOf"]) == 7
    assert set(output_schema["properties"]["status"]["enum"]) == {
        "accepted",
        "rejected",
        "route_back",
        "waived",
        "typed_blocker",
        "human_gate",
        "invalid_host_input",
    }
