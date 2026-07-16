from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from med_autoscience.authority_handlers.paper_mission import (
    evaluate_paper_mission_authority,
)
from med_autoscience.authority_handlers._generation_manifest import (
    build_generation_manifest_v2,
    normalize_generation_manifest,
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


def _authorize_reused_lane(
    current: dict[str, Any],
    origin: dict[str, Any],
    lane: str,
    authority_records: Any,
) -> None:
    origin_wrapper = next(
        item
        for item in origin["generation_manifest"]["independent_review_receipts"]
        if item["receipt"]["review_lane"] == lane
    )
    current["generation_manifest"]["independent_review_receipts"] = [
        deepcopy(origin_wrapper)
        if item["receipt"]["review_lane"] == lane
        else item
        for item in current["generation_manifest"]["independent_review_receipts"]
    ]
    lane_state = next(
        item
        for item in current["review_authority"]["currentness_receipt"][
            "lane_currentness"
        ]
        if item["review_lane"] == lane
    )
    receipt = origin_wrapper["receipt"]
    lane_state.update(
        {
            "review_authority_epoch": receipt["authority_epoch"],
            "currentness_status": "reused_unchanged_scope",
            "review_scope_sha256": next(
                item["review_scope_sha256"]
                for item in current["generation_manifest"]["review_scopes"]
                if item["review_lane"] == lane
            ),
            "review_receipt_issued_generation_id": receipt[
                "issued_generation_id"
            ],
            "review_receipt_issued_generation_manifest_sha256": receipt[
                "issued_generation_manifest_sha256"
            ],
            "current_review_request_ref": deepcopy(receipt["review_request_ref"]),
            "current_review_receipt_ref": deepcopy(origin_wrapper["receipt_ref"]),
            "reuse_provenance": {
                "origin_generation_id": origin["generation_manifest"]["generation_id"],
                "origin_generation_manifest_ref": deepcopy(
                    origin["generation_manifest_ref"]
                ),
                "origin_review_request_ref": deepcopy(receipt["review_request_ref"]),
                "origin_review_receipt_ref": deepcopy(origin_wrapper["receipt_ref"]),
                "origin_review_scope_sha256": receipt["review_scope_sha256"],
                "origin_candidate_admission_receipt_refs": deepcopy(
                    receipt["accepted_candidate_receipt_refs"]
                ),
            },
        }
    )
    authority_records.reseal_review_currentness(current)


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


def test_v2_review_scopes_are_mas_owned_generation_independent_and_exact_byte_full(
    authority_records: Any,
) -> None:
    first = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        manifest_version=2,
        generation_id="study-generation-003",
    )
    second = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        manifest_version=2,
        generation_id="study-generation-004",
    )

    first_result = _evaluate(first)
    assert first_result["status"] == "owner_receipt"
    assert _evaluate(second)["status"] == "owner_receipt"
    _output_validator().validate(first_result)
    transport = first_result["owner_receipt"]["artifact_projection_transport"]
    assert "member_id" not in transport["projection_manifest_ref"]
    assert all(
        "member_id" not in item
        for item in transport["generation_bound_truth_members"]
    )
    first_scopes = {
        item["review_lane"]: item for item in first["generation_manifest"]["review_scopes"]
    }
    second_scopes = {
        item["review_lane"]: item
        for item in second["generation_manifest"]["review_scopes"]
    }
    for lane in {"medical", "statistical", "reference", "display", "publication"}:
        assert (
            first_scopes[lane]["review_scope_sha256"]
            == second_scopes[lane]["review_scope_sha256"]
        )
        roles = {item["role"] for item in first_scopes[lane]["reviewed_members"]}
        assert "source_input_digest" not in roles
        assert "candidate_admission_receipt" not in roles
    assert (
        first_scopes["exact_byte_package"]["reviewed_members"]
        == first["generation_manifest"]["artifacts"]
    )
    assert (
        first_scopes["exact_byte_package"]["review_scope_sha256"]
        != second_scopes["exact_byte_package"]["review_scope_sha256"]
    )

    forged = deepcopy(first)
    medical = next(
        item
        for item in forged["generation_manifest"]["review_scopes"]
        if item["review_lane"] == "medical"
    )
    medical["reviewed_members"] = medical["reviewed_members"][:-1]
    result = _evaluate(forged)
    assert result["status"] == "invalid_host_input"
    assert "MAS-owned lane inventory" in result["error"]["detail"]


def test_v2_public_manifest_builder_is_canonical_receipt_free_and_fail_closed(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        manifest_version=2,
    )
    artifacts = request["generation_manifest"]["artifacts"]
    built = build_generation_manifest_v2(
        artifacts=list(reversed(artifacts)),
        generation_id="public-builder-generation",
        manifest_scope="publication_generation",
    )
    rebuilt = build_generation_manifest_v2(
        artifacts=artifacts,
        generation_id="public-builder-generation",
        manifest_scope=" publication_generation ",
    )

    assert built == rebuilt
    assert built["independent_review_receipts"] == []
    assert [
        item["review_lane"] for item in built["review_scopes"]
    ] == sorted(
        {
            "medical",
            "statistical",
            "reference",
            "display",
            "publication",
            "exact_byte_package",
        }
    )
    assert normalize_generation_manifest(built)[
        "generation_manifest_sha256"
    ] == built["generation_manifest_sha256"]

    duplicate = deepcopy(artifacts)
    duplicate[1]["member_id"] = duplicate[0]["member_id"]
    with pytest.raises(ValueError, match="duplicate member_id"):
        build_generation_manifest_v2(
            artifacts=duplicate,
            generation_id="duplicate-member-generation",
            manifest_scope="publication_generation",
        )
    with pytest.raises(ValueError, match="must be one of"):
        build_generation_manifest_v2(
            artifacts=artifacts,
            generation_id="invalid-scope-generation",
            manifest_scope="not_a_manifest_scope",
        )
    with pytest.raises(ValueError, match="must be a non-empty string"):
        build_generation_manifest_v2(
            artifacts=artifacts,
            generation_id="unhashable-scope-generation",
            manifest_scope=[],  # type: ignore[arg-type]
        )


def test_v2_scope_dependency_map_selectively_invalidates_only_affected_lanes(
    authority_records: Any,
) -> None:
    baseline = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        manifest_version=2,
        generation_id="study-generation-003",
    )
    baseline_scopes = {
        item["review_lane"]: item["review_scope_sha256"]
        for item in baseline["generation_manifest"]["review_scopes"]
    }
    cases = {
        "figure_file": {"display", "publication", "exact_byte_package"},
        "canonical_manuscript": {
            "medical",
            "statistical",
            "reference",
            "publication",
            "exact_byte_package",
        },
        "analysis_output": {"medical", "statistical", "exact_byte_package"},
        "reference_library": {"reference", "publication", "exact_byte_package"},
        "final_zip_member": {"exact_byte_package"},
    }
    for role, expected_changed_lanes in cases.items():
        changed = authority_records.paper_request(
            scope="publication_generation",
            stage_id="finalize_and_publication_handoff",
            manifest_version=2,
            generation_id=f"study-generation-changed-{role}",
            artifact_sha_overrides={
                role: authority_records.digest(f"changed-{role}-bytes")
            },
        )
        changed_scopes = {
            item["review_lane"]: item["review_scope_sha256"]
            for item in changed["generation_manifest"]["review_scopes"]
        }
        assert {
            lane
            for lane, digest in changed_scopes.items()
            if digest != baseline_scopes[lane]
        } == expected_changed_lanes


def test_v2_professional_scope_is_locator_invariant_but_member_identity_sensitive(
    authority_records: Any,
) -> None:
    baseline = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        manifest_version=2,
        generation_id="study-generation-scope-baseline",
    )
    renamed = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        manifest_version=2,
        generation_id="study-generation-scope-renamed",
        artifact_ref_overrides={
            "figure_file": "workspace://study/figures/renamed-figure"
        },
    )
    replaced_identity = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        manifest_version=2,
        generation_id="study-generation-scope-replaced-identity",
        artifact_member_id_overrides={
            "figure_file": "mas-member:figure_file:replacement"
        },
    )

    def scope_digests(request: dict[str, Any]) -> dict[str, str]:
        return {
            item["review_lane"]: item["review_scope_sha256"]
            for item in request["generation_manifest"]["review_scopes"]
        }

    baseline_digests = scope_digests(baseline)
    renamed_digests = scope_digests(renamed)
    replacement_digests = scope_digests(replaced_identity)
    for lane in {"medical", "statistical", "reference", "display", "publication"}:
        assert renamed_digests[lane] == baseline_digests[lane]
    assert (
        renamed_digests["exact_byte_package"]
        != baseline_digests["exact_byte_package"]
    )
    for lane in {"display", "publication", "exact_byte_package"}:
        assert replacement_digests[lane] != baseline_digests[lane]
    assert _evaluate(renamed)["status"] == "owner_receipt"
    assert _evaluate(replaced_identity)["status"] == "owner_receipt"


def test_v2_member_order_is_canonical_and_member_id_is_required_unique(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        manifest_version=2,
    )
    reordered = deepcopy(request)
    manifest = reordered["generation_manifest"]
    manifest["artifacts"].reverse()
    manifest["review_scopes"].reverse()
    for scope in manifest["review_scopes"]:
        scope["reviewed_members"].reverse()
    manifest["independent_review_receipts"].reverse()
    for wrapper in manifest["independent_review_receipts"]:
        wrapper["receipt"]["reviewed_members"].reverse()
    reordered["review_authority"]["currentness_receipt"][
        "lane_currentness"
    ].reverse()
    assert _evaluate(reordered) == _evaluate(request)

    missing = deepcopy(request)
    missing["generation_manifest"]["artifacts"][0].pop("member_id")
    result = _evaluate(missing)
    assert result["status"] == "invalid_host_input"
    assert "missing fields: member_id" in result["error"]["detail"]

    duplicate_root = deepcopy(request)
    root_members = duplicate_root["generation_manifest"]["artifacts"]
    root_members[1]["member_id"] = root_members[0]["member_id"]
    result = _evaluate(duplicate_root)
    assert result["status"] == "invalid_host_input"
    assert "duplicate member_id" in result["error"]["detail"]

    duplicate_review = deepcopy(request)
    exact_scope = next(
        item
        for item in duplicate_review["generation_manifest"]["review_scopes"]
        if item["review_lane"] == "exact_byte_package"
    )
    exact_scope["reviewed_members"][1]["member_id"] = exact_scope[
        "reviewed_members"
    ][0]["member_id"]
    result = _evaluate(duplicate_review)
    assert result["status"] == "invalid_host_input"
    assert "duplicate member_id" in result["error"]["detail"]


def test_v2_currentness_reuses_only_exact_unchanged_lane_scopes(
    authority_records: Any,
) -> None:
    origin = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        manifest_version=2,
        generation_id="study-generation-003",
    )
    current = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        manifest_version=2,
        generation_id="study-generation-004",
        artifact_sha_overrides={
            "figure_file": authority_records.digest("changed-figure-bytes")
        },
    )
    origin_reviews = {
        item["receipt"]["review_lane"]: item
        for item in origin["generation_manifest"]["independent_review_receipts"]
    }
    for lane in ("medical", "statistical", "reference"):
        _authorize_reused_lane(current, origin, lane, authority_records)
    assert _evaluate(current)["status"] == "owner_receipt"

    forged = deepcopy(current)
    forged_reviews = {
        item["receipt"]["review_lane"]: item
        for item in forged["generation_manifest"]["independent_review_receipts"]
    }
    forged_reviews["display"] = deepcopy(origin_reviews["display"])
    forged["generation_manifest"]["independent_review_receipts"] = list(
        forged_reviews.values()
    )
    forged_display = next(
        item
        for item in forged["review_authority"]["currentness_receipt"][
            "lane_currentness"
        ]
        if item["review_lane"] == "display"
    )
    old_display_receipt = origin_reviews["display"]["receipt"]
    forged_display.update(
        {
            "review_authority_epoch": old_display_receipt["authority_epoch"],
            "current_review_request_ref": deepcopy(
                old_display_receipt["review_request_ref"]
            ),
            "current_review_receipt_ref": deepcopy(
                origin_reviews["display"]["receipt_ref"]
            ),
            "review_receipt_issued_generation_id": old_display_receipt[
                "issued_generation_id"
            ],
            "review_receipt_issued_generation_manifest_sha256": old_display_receipt[
                "issued_generation_manifest_sha256"
            ],
        }
    )
    authority_records.reseal_review_currentness(forged)
    result = _evaluate(forged)
    assert result["status"] == "route_back"
    assert result["route_back"]["reason_code"] == (
        "independent_review_receipt_not_current"
    )


def test_v2_rubric_change_invalidates_only_the_affected_reused_lane(
    authority_records: Any,
) -> None:
    origin = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        manifest_version=2,
        generation_id="study-generation-before-rubric-change",
    )
    current = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        manifest_version=2,
        generation_id="study-generation-after-rubric-change",
    )
    _authorize_reused_lane(current, origin, "medical", authority_records)
    medical_currentness = next(
        item
        for item in current["review_authority"]["currentness_receipt"][
            "lane_currentness"
        ]
        if item["review_lane"] == "medical"
    )
    medical_currentness["current_rubric_ref"] = authority_records.typed_ref(
        "mas_quality_rubric", "medical-rubric-v2"
    )
    authority_records.reseal_review_currentness(current)

    result = _evaluate(current)

    assert result["status"] == "route_back"
    assert result["route_back"]["reason_code"] == (
        "independent_review_receipt_not_current"
    )
    assert result["route_back"]["affected_review_lanes"] == [
        {
            "review_lane": "medical",
            "reason_code": "independent_review_receipt_not_current",
            "resume_condition": (
                "replace stale medical lane currentness and receipt bindings"
            ),
        }
    ]


def test_v2_currentness_returns_all_affected_review_lanes_in_one_route_back(
    authority_records: Any,
) -> None:
    origin = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        manifest_version=2,
        generation_id="study-generation-before-figure-change",
    )
    current = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        manifest_version=2,
        generation_id="study-generation-after-figure-change",
        artifact_sha_overrides={
            "figure_file": authority_records.digest("changed-figure-bytes")
        },
    )
    for lane in ("display", "publication", "exact_byte_package"):
        _authorize_reused_lane(current, origin, lane, authority_records)

    result = _evaluate(current)

    assert result["status"] == "route_back"
    assert result["route_back"]["reason_code"] == (
        "independent_review_receipt_not_current"
    )
    assert result["route_back"]["resume_condition"] == (
        "refresh all affected review lanes in one pass: "
        "display, publication, exact_byte_package"
    )
    assert [
        item["review_lane"]
        for item in result["route_back"]["affected_review_lanes"]
    ] == ["display", "publication", "exact_byte_package"]
    assert {
        item["reason_code"]
        for item in result["route_back"]["affected_review_lanes"]
    } == {"independent_review_receipt_not_current"}
    _output_validator().validate(result)


def test_v2_old_receipt_with_removed_optional_member_routes_by_lane(
    authority_records: Any,
) -> None:
    extra_evidence = {
        "member_id": "mas-member:evidence_record:retired-secondary",
        "role": "evidence_record",
        "ref": "mas-evidence://retired-secondary-evidence",
        "size_bytes": 811,
        "sha256": authority_records.digest("retired-secondary-evidence-bytes"),
    }
    origin = authority_records.paper_request(
        manifest_version=2,
        generation_id="study-generation-with-extra-evidence",
        extra_artifacts=[extra_evidence],
    )
    current = authority_records.paper_request(
        manifest_version=2,
        generation_id="study-generation-without-extra-evidence",
    )
    _authorize_reused_lane(current, origin, "reference", authority_records)

    result = _evaluate(current)

    assert result["status"] == "route_back"
    assert result["route_back"]["reason_code"] == (
        "independent_review_receipt_not_current"
    )


def test_manifest_and_review_currentness_versions_cannot_be_mixed(
    authority_records: Any,
) -> None:
    v1 = authority_records.paper_request()
    v2 = authority_records.paper_request(manifest_version=2)
    assert _evaluate(v1)["status"] == "owner_receipt"
    assert _evaluate(v2)["status"] == "owner_receipt"

    v2_manifest_v1_currentness = deepcopy(v2)
    old_currentness = deepcopy(v1["review_authority"]["currentness_receipt"])
    old_currentness.update(
        {
            "current_generation_id": v2["generation_manifest"]["generation_id"],
            "current_generation_manifest_ref": deepcopy(v2["generation_manifest_ref"]),
            "current_review_request_ref": deepcopy(
                v2["review_authority"]["review_request_ref"]
            ),
            "current_candidate_admission_receipt_refs": [
                deepcopy(v2["candidate_admissions"][0]["receipt_ref"])
            ],
            "current_review_receipt_refs": [
                deepcopy(item["receipt_ref"])
                for item in v2["generation_manifest"]["independent_review_receipts"]
            ],
        }
    )
    v2_manifest_v1_currentness["review_authority"]["currentness_receipt"] = (
        old_currentness
    )
    authority_records.reseal_review_currentness(v2_manifest_v1_currentness)
    result = _evaluate(v2_manifest_v1_currentness)
    assert result["status"] == "invalid_host_input"
    assert "schema versions must match" in result["error"]["detail"]

    v1_manifest_v2_currentness = deepcopy(v1)
    v1_manifest_v2_currentness["review_authority"] = deepcopy(v2["review_authority"])
    result = _evaluate(v1_manifest_v2_currentness)
    assert result["status"] == "invalid_host_input"
    assert "schema versions must match" in result["error"]["detail"]


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
    candidate_validator.validate(
        authority_records.candidate_request(manifest_version=2)
    )
    paper_validator.validate(
        authority_records.paper_request(manifest_version=2)
    )
    paper_validator.validate(
        authority_records.paper_request(
            scope="publication_generation",
            stage_id="finalize_and_publication_handoff",
            manifest_version=2,
        )
    )

    v1_paper = authority_records.paper_request()
    v2_paper = authority_records.paper_request(manifest_version=2)
    v1_manifest_v2_currentness = deepcopy(v1_paper)
    v1_manifest_v2_currentness["review_authority"] = deepcopy(
        v2_paper["review_authority"]
    )
    assert list(paper_validator.iter_errors(v1_manifest_v2_currentness))

    v2_manifest_v1_currentness = deepcopy(v2_paper)
    v2_manifest_v1_currentness["review_authority"] = deepcopy(
        v1_paper["review_authority"]
    )
    assert list(paper_validator.iter_errors(v2_manifest_v1_currentness))

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
