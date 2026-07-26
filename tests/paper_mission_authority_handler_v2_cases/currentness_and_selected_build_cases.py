from __future__ import annotations

from .shared import *

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
    assert receipt["schema_version"] == 3
    assert receipt["owner"] == "MedAutoScience"
    assert receipt["authorizes_stage_domain_completion"] is True
    assert receipt["authorizes_publication_or_submission"] is False
    assert (
        receipt["generation_identity"]["generation_manifest_ref"]
        == request["generation_manifest_ref"]
    )
    assert receipt["selected_build_currentness_authority_ref"] == request[
        "selected_build_currentness_authority"
    ]["authority_ref"]
    assert (
        receipt["accepted_candidate_admissions"][0]["claim_scope"]
        == request["candidate_admissions"][0]["receipt"]["claim_scope"]
    )
    assert len(receipt["independent_review_receipt_refs"]) == 4


def test_origin_main_legacy_owner_receipt_v2_preserves_full_object_and_exact_id(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request(
        include_revision_generation_bindings=False
    )
    result = _evaluate(request)
    receipt = result["owner_receipt"]

    assert result["status"] == "owner_receipt"
    assert receipt["schema_version"] == 2
    assert "selected_build_currentness_authority_ref" not in receipt
    assert set(receipt) == {
        "accepted_candidate_admissions",
        "artifact_lineage_refs",
        "authorizes_publication_or_submission",
        "authorizes_stage_domain_completion",
        "claim_boundary_ref",
        "failed_path_refs",
        "generation_identity",
        "host_refs",
        "independent_review_receipt_refs",
        "medical_evidence_refs",
        "mission_identity",
        "negative_result_refs",
        "owner",
        "professional_skill_receipt_projection",
        "receipt_fingerprint",
        "receipt_id",
        "receipt_kind",
        "receipt_size_bytes",
        "reproducibility_refs",
        "requires_host_exact_byte_persistence",
        "review_authority_epoch",
        "review_currentness_receipt_ref",
        "revision_consumption",
        "schema_version",
        "source_readiness_receipt_ref",
        "verdict",
    }
    assert receipt["receipt_id"] == (
        "mas-paper-mission-owner-receipt:"
        "0b7cdfe2e2ab9118cf13be7c91dcd2750878a236905f9e8d15494b52bbbaea8b"
    )
    assert receipt["receipt_size_bytes"] == 12539
    assert receipt["receipt_fingerprint"] == (
        "sha256:0b7cdfe2e2ab9118cf13be7c91dcd2750878a236905f9e8d15494b52bbbaea8b"
    )
    assert authority_records.digest(authority_records.canonical_bytes(receipt)) == (
        "sha256:cab413f1beaf25967c87e864c97a14cdc1f742b057fa15bc15ba903bd0d10e55"
    )
    _output_validator().validate(result)


def test_owner_receipt_schema_oneof_enforces_legacy_v2_and_selected_build_v3(
    authority_records: Any,
) -> None:
    validator = _output_validator()
    v3 = _evaluate(authority_records.paper_request())
    validator.validate(v3)
    assert v3["owner_receipt"]["schema_version"] == 3

    missing_v3_authority = deepcopy(v3)
    del missing_v3_authority["owner_receipt"][
        "selected_build_currentness_authority_ref"
    ]
    assert list(validator.iter_errors(missing_v3_authority))

    v3_mislabeled_as_v2 = deepcopy(v3)
    v3_mislabeled_as_v2["owner_receipt"]["schema_version"] = 2
    assert list(validator.iter_errors(v3_mislabeled_as_v2))

    tampered_v3_authority = deepcopy(v3)
    tampered_v3_authority["owner_receipt"][
        "selected_build_currentness_authority_ref"
    ]["kind"] = "mas_artifact"
    assert list(validator.iter_errors(tampered_v3_authority))

    v2 = _evaluate(
        authority_records.paper_request(
            include_revision_generation_bindings=False
        )
    )
    validator.validate(v2)
    v2_with_v3_field = deepcopy(v2)
    v2_with_v3_field["owner_receipt"][
        "selected_build_currentness_authority_ref"
    ] = deepcopy(v3["owner_receipt"]["selected_build_currentness_authority_ref"])
    assert list(validator.iter_errors(v2_with_v3_field))


def test_current_internal_validation_first_draft_uses_exact_scholar_receipts(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request()
    manifest = request["generation_manifest"]
    application = manifest["first_draft_quality_application"]

    assert application["schema_version"] == 2
    assert application["validation_design"] == "internal_validation"
    assert application["triggers"]["uses_clinical_or_registry_data"] is True
    assert application["candidate_dispositions"][
        "external_transportability_ref"
    ]["status"] == "not_applicable_with_reason"
    assert application["candidate_refs"]["external_transportability_ref"] is None
    assert any(item["role"] == "pdf" for item in manifest["artifacts"])

    invocations = manifest["professional_skill_invocations"]
    assert all(item["schema_version"] == 2 for item in invocations)
    assert all(
        {"invocation_ref", "receipt_ref", "input_artifact_bindings"}
        <= set(item)
        for item in invocations
    )
    skill_ids = {item["skill_id"] for item in invocations}
    assert "medical-data-freeze-and-analysis-readiness-reviewer" in skill_ids
    assert "medical-survival-analysis-plan" in skill_ids
    assert "medical-display-qc" in skill_ids
    assert "medical-risk-model-transportability-reviewer" not in skill_ids
    _schema_validator("mas-evidence-generation-manifest.schema.json").validate(
        manifest
    )
    result = _evaluate(request)
    assert result["status"] == "owner_receipt"
    projected = result["owner_receipt"]["professional_skill_receipt_projection"]
    assert {
        (item["skill_id"], item["invocation_ref"]["sha256"], item["receipt_ref"]["sha256"])
        for item in projected
    } == {
        (item["skill_id"], item["invocation_ref"]["sha256"], item["receipt_ref"]["sha256"])
        for item in invocations
    }


def test_reviewer_revision_requires_current_selected_build_and_response_sync(
    authority_records: Any,
) -> None:
    current = authority_records.paper_request()
    authority_records.bind_revision_consumption(current)
    assert _evaluate(current)["status"] == "owner_receipt"

    legacy = authority_records.paper_request(
        include_revision_generation_bindings=False
    )
    assert _evaluate(legacy)["status"] == "owner_receipt"
    authority_records.bind_revision_consumption(legacy)
    route = _assert_progress_debt(
        _evaluate(legacy), "selected_build_binding_missing"
    )
    assert route["next_owner"] == "manuscript_authoring"

    stale = authority_records.paper_request(dependency_currentness="stale")
    authority_records.bind_revision_consumption(stale)
    result = _evaluate(stale)
    assert result["status"] == "invalid_host_input"
    assert "selected build dependencies must be current" in result["error"][
        "detail"
    ]

    unsynchronized = authority_records.paper_request(
        reviewer_response_sync_status="route_back_required"
    )
    authority_records.bind_revision_consumption(unsynchronized)
    _assert_progress_debt(
        _evaluate(unsynchronized), "reviewer_response_sync_route_back_required"
    )


@pytest.mark.parametrize("dependency_currentness", ["stale", "open"])
def test_selected_build_currentness_fails_closed_without_revision_consumption(
    authority_records: Any,
    dependency_currentness: str,
) -> None:
    request = authority_records.paper_request(
        dependency_currentness=dependency_currentness
    )

    result = _evaluate(request)

    assert result["status"] == "invalid_host_input"
    assert "selected build dependencies must be current" in result["error"][
        "detail"
    ]


def test_selected_build_root_epoch_and_dependency_authority_mismatch_fail_closed(
    authority_records: Any,
) -> None:
    root_mismatch = authority_records.paper_request()
    root_mismatch["generation_manifest"]["selected_build_binding"][
        "root_matches_selected_bytes"
    ] = False
    authority_records.reseal_selected_build_currentness_receipt(root_mismatch)
    authority_records.refresh_paper_manifest_identity(root_mismatch)
    result = _evaluate(root_mismatch)
    assert result["status"] == "invalid_host_input"
    assert "root_matches_selected_bytes does not match exact reader bytes" in result["error"][
        "detail"
    ]

    epoch_mismatch = authority_records.paper_request()
    epoch_mismatch["selected_build_currentness_authority"]["authority_record"][
        "authority_epoch"
    ] = "mas-authority-epoch:stale"
    authority_records.reseal_selected_build_currentness_authority(epoch_mismatch)
    epoch_mismatch["host_context"][
        "build_dependency_currentness_authority_ref"
    ] = deepcopy(epoch_mismatch["selected_build_currentness_authority"]["authority_ref"])
    authority_records.reseal_review_currentness(epoch_mismatch)
    result = _evaluate(epoch_mismatch)
    assert result["status"] == "invalid_host_input"
    assert "authority epoch is not current" in result["error"]["detail"]

    dependency_mismatch = authority_records.paper_request()
    dependency_mismatch["selected_build_currentness_authority"]["authority_record"][
        "dependency_manifest_ref"
    ] = authority_records.exact_ref("mas_artifact", "stale-dependency-manifest")
    authority_records.reseal_selected_build_currentness_authority(
        dependency_mismatch
    )
    dependency_mismatch["host_context"][
        "build_dependency_currentness_authority_ref"
    ] = deepcopy(
        dependency_mismatch["selected_build_currentness_authority"]["authority_ref"]
    )
    authority_records.reseal_review_currentness(dependency_mismatch)
    result = _evaluate(dependency_mismatch)
    assert result["status"] == "invalid_host_input"
    assert "dependency manifest is not current" in result["error"]["detail"]


def test_selected_build_and_response_bindings_fail_closed_on_exact_ref_tamper(
    authority_records: Any,
) -> None:
    reader_mismatch = authority_records.paper_request()
    selected_reader = next(
        item
        for item in reader_mismatch["generation_manifest"]["artifacts"]
        if item["role"] == "selected_reader_output"
    )
    selected_reader["sha256"] = authority_records.digest(
        "different-selected-reader-bytes"
    )
    reader_mismatch["generation_manifest"]["selected_build_binding"][
        "selected_reader_output_ref"
    ]["sha256"] = selected_reader["sha256"]
    reader_mismatch["generation_manifest"]["review_scopes"] = build_review_scopes(
        reader_mismatch["generation_manifest"]["artifacts"],
        "manuscript_generation",
    )
    result = _evaluate(reader_mismatch)
    assert result["status"] == "invalid_host_input"
    assert "does not match exact reader bytes" in result["error"]["detail"]

    stale_build_ref = authority_records.paper_request()
    dependency = next(
        item
        for item in stale_build_ref["generation_manifest"]["artifacts"]
        if item["role"] == "build_dependency_manifest"
    )
    dependency["sha256"] = authority_records.digest("changed-dependency-bytes")
    stale_build_ref["generation_manifest"]["review_scopes"] = build_review_scopes(
        stale_build_ref["generation_manifest"]["artifacts"],
        "manuscript_generation",
    )
    result = _evaluate(stale_build_ref)
    assert result["status"] == "invalid_host_input"
    assert "must match exactly one current" in result["error"]["detail"]

    forged_currentness = authority_records.paper_request()
    forged_currentness["generation_manifest"]["selected_build_binding"][
        "dependency_currentness_receipt_ref"
    ]["kind"] = "mas_artifact"
    result = _evaluate(forged_currentness)
    assert result["status"] == "invalid_host_input"
    assert "kind must be mas_build_dependency_currentness_receipt" in result["error"][
        "detail"
    ]

    unexpanded_currentness = authority_records.paper_request()
    del unexpanded_currentness["generation_manifest"]["selected_build_binding"][
        "dependency_currentness_receipt"
    ]
    result = _evaluate(unexpanded_currentness)
    assert result["status"] == "invalid_host_input"
    assert "missing fields: dependency_currentness_receipt" in result["error"][
        "detail"
    ]

    wrong_receipt_kind = authority_records.paper_request()
    wrong_receipt_kind["generation_manifest"]["selected_build_binding"][
        "dependency_currentness_receipt"
    ]["receipt_kind"] = "mas_artifact"
    result = _evaluate(wrong_receipt_kind)
    assert result["status"] == "invalid_host_input"
    assert "receipt_kind is invalid" in result["error"]["detail"]

    forged_receipt_hash = authority_records.paper_request()
    forged_receipt_hash["generation_manifest"]["selected_build_binding"][
        "dependency_currentness_receipt"
    ]["receipt_fingerprint"] = authority_records.digest("forged-currentness")
    result = _evaluate(forged_receipt_hash)
    assert result["status"] == "invalid_host_input"
    assert "receipt_fingerprint is invalid" in result["error"]["detail"]

    mismatched_receipt_status = authority_records.paper_request()
    receipt = mismatched_receipt_status["generation_manifest"][
        "selected_build_binding"
    ]["dependency_currentness_receipt"]
    receipt["dependency_currentness"] = "stale"
    result = _evaluate(mismatched_receipt_status)
    assert result["status"] == "invalid_host_input"
    assert "does not match selected build binding" in result["error"]["detail"]

    mismatched_receipt_dependency = authority_records.paper_request()
    receipt = mismatched_receipt_dependency["generation_manifest"][
        "selected_build_binding"
    ]["dependency_currentness_receipt"]
    receipt["dependency_manifest_ref"] = authority_records.exact_ref(
        "mas_artifact", "different-dependency-manifest"
    )
    result = _evaluate(mismatched_receipt_dependency)
    assert result["status"] == "invalid_host_input"
    assert "dependency_manifest_ref does not match selected build binding" in result[
        "error"
    ]["detail"]

    stale_affected_member = authority_records.paper_request()
    stale_affected_member["generation_manifest"]["reviewer_response_sync"][
        "items"
    ][0]["affected_artifact_bindings"][0]["sha256"] = authority_records.digest(
        "stale-affected-manuscript-bytes"
    )
    result = _evaluate(stale_affected_member)
    assert result["status"] == "invalid_host_input"
    assert "must match exactly one current manifest artifact" in result["error"][
        "detail"
    ]


def test_selected_build_currentness_requires_separate_current_owner_authority(
    authority_records: Any,
) -> None:
    missing_authority = authority_records.paper_request()
    del missing_authority["selected_build_currentness_authority"]
    result = _evaluate(missing_authority)
    assert result["status"] == "invalid_host_input"
    assert "selected_build_currentness_authority is required" in result["error"][
        "detail"
    ]

    self_sealed_receipt = authority_records.paper_request()
    selected_build = self_sealed_receipt["generation_manifest"][
        "selected_build_binding"
    ]
    selected_build["dependency_currentness_receipt"]["authority_ref"] = (
        authority_records.exact_ref(
            "mas_build_dependency_currentness_authority",
            "producer-self-declared-authority",
        )
    )
    authority_records.reseal_selected_build_currentness_receipt(self_sealed_receipt)
    authority_records.refresh_paper_manifest_identity(self_sealed_receipt)
    result = _evaluate(self_sealed_receipt)
    assert result["status"] == "invalid_host_input"
    assert "does not bind the current owner authority record" in result["error"][
        "detail"
    ]

    authority_not_current = authority_records.paper_request()
    authority_not_current["review_authority"]["currentness_receipt"][
        "current_build_dependency_authority_refs"
    ] = []
    authority_records.reseal_review_currentness(authority_not_current)
    result = _evaluate(authority_not_current)
    assert result["status"] == "invalid_host_input"
    assert "is not current in the MAS authority record" in result["error"]["detail"]

    producer_issued_authority = authority_records.paper_request()
    producer_issued_authority["selected_build_currentness_authority"][
        "authority_record"
    ]["issuer_attempt_ref"] = deepcopy(
        producer_issued_authority["host_context"]["producer_attempt_ref"]
    )
    authority_records.reseal_selected_build_currentness_authority(
        producer_issued_authority
    )
    result = _evaluate(producer_issued_authority)
    assert result["status"] == "invalid_host_input"
    assert "does not match host-bound authority ref" in result["error"]["detail"]

    forged_distinct_issuer = authority_records.paper_request()
    forged_distinct_issuer["selected_build_currentness_authority"][
        "authority_record"
    ]["issuer_attempt_ref"] = authority_records.typed_ref(
        "opl_stage_attempt", "arbitrary-forged-currentness-owner"
    )
    authority_records.reseal_selected_build_currentness_authority(
        forged_distinct_issuer
    )
    result = _evaluate(forged_distinct_issuer)
    assert result["status"] == "invalid_host_input"
    assert "does not match host-bound authority ref" in result["error"]["detail"]


def test_reviewer_response_requires_exact_evidence_and_action_matrix_coverage(
    authority_records: Any,
) -> None:
    for status in ("implemented_candidate", "independently_reviewed_candidate"):
        missing_evidence = authority_records.paper_request(
            reviewer_response_item_status=status
        )
        missing_evidence["generation_manifest"]["reviewer_response_sync"]["items"][
            0
        ]["evidence_refs"] = []
        result = _evaluate(missing_evidence)
        assert result["status"] == "invalid_host_input"
        assert "requires exact evidence refs" in result["error"]["detail"]

    incomplete_coverage = authority_records.paper_request()
    incomplete_coverage["generation_manifest"]["reviewer_response_sync"][
        "action_matrix_item_ids"
    ].append("REV-002")
    result = _evaluate(incomplete_coverage)
    assert result["status"] == "invalid_host_input"
    assert "must exactly cover action_matrix_item_ids" in result["error"]["detail"]


def test_independently_reviewed_response_binds_current_manifest_review_receipt(
    authority_records: Any,
) -> None:
    generic_evidence = authority_records.paper_request(
        reviewer_response_item_status="independently_reviewed_candidate"
    )
    result = _evaluate(generic_evidence)
    assert result["status"] == "invalid_host_input"
    assert "requires current independent reviewer receipt refs" in result["error"][
        "detail"
    ]

    current_review = authority_records.paper_request()
    current_review["generation_manifest"]["reviewer_response_sync"]["items"][0][
        "status"
    ] = "independently_reviewed_candidate"
    current_review["generation_manifest"]["reviewer_response_sync"]["items"][0][
        "evidence_refs"
    ] = [
        deepcopy(
            current_review["generation_manifest"]["independent_review_receipts"][0][
                "receipt_ref"
            ]
        )
    ]
    authority_records.refresh_paper_manifest_identity(current_review)
    normalized = normalize_generation_manifest(current_review["generation_manifest"])
    assert normalized["reviewer_response_sync"]["items"][0]["evidence_refs"] == [
        current_review["generation_manifest"]["independent_review_receipts"][0][
            "receipt_ref"
        ]
    ]

    stale_review = deepcopy(current_review)
    stale_review["generation_manifest"]["reviewer_response_sync"]["items"][0][
        "evidence_refs"
    ][0]["sha256"] = authority_records.digest("stale-independent-review")
    authority_records.refresh_paper_manifest_identity(stale_review)
    result = _evaluate(stale_review)
    assert result["status"] == "invalid_host_input"
    assert "must bind a current manifest independent reviewer receipt" in result[
        "error"
    ]["detail"]


def test_frozen_response_uses_external_synthesis_or_new_revision_lineage(
    authority_records: Any,
) -> None:
    synthesis = authority_records.paper_request(
        reviewer_response_candidate_state="frozen",
        reviewer_response_post_freeze_disposition="external_synthesis_bound",
    )
    authority_records.bind_revision_consumption(synthesis)
    assert _evaluate(synthesis)["status"] == "owner_receipt"

    scientific_change = authority_records.paper_request(
        reviewer_response_candidate_state="frozen",
        reviewer_response_post_freeze_disposition=(
            "scientific_change_requires_new_revision"
        ),
    )
    authority_records.bind_revision_consumption(scientific_change)
    _assert_progress_debt(
        _evaluate(scientific_change),
        "post_freeze_scientific_change_requires_new_revision_cycle",
    )

    missing_lineage = authority_records.paper_request(
        reviewer_response_candidate_state="frozen",
        reviewer_response_post_freeze_disposition=(
            "scientific_change_requires_new_revision"
        ),
    )
    missing_lineage["generation_manifest"]["reviewer_response_sync"][
        "new_revision_ref"
    ] = None
    result = _evaluate(missing_lineage)
    assert result["status"] == "invalid_host_input"
    assert "scientific response change requires new_revision_ref" in result["error"][
        "detail"
    ]


def test_early_analysis_revision_is_not_preempted_by_authoring_bindings(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request(
        scope="analysis_generation",
        stage_id="bounded_analysis_campaign",
        manifest_version=2,
    )
    authority_records.bind_revision_consumption(request)
    result = _evaluate(request)
    assert result["route_back"]["reason_code"] == (
        "candidate_admission_receipt_required"
    )
    assert "selected_build" not in result["route_back"]["reason_code"]

    higher_scope = authority_records.paper_request(
        scope="manuscript_generation",
        stage_id="bounded_analysis_campaign",
        manifest_version=2,
        include_first_draft_quality_application=False,
        include_revision_generation_bindings=False,
    )
    authority_records.bind_revision_consumption(higher_scope)
    result = _evaluate(higher_scope)
    assert result["status"] == "owner_receipt"


def test_revision_roles_are_visible_in_immutable_review_scopes(
    authority_records: Any,
) -> None:
    manuscript = authority_records.paper_request()["generation_manifest"]
    scope_roles = {
        scope["review_lane"]: {item["role"] for item in scope["reviewed_members"]}
        for scope in manuscript["review_scopes"]
    }
    assert {
        "reviewer_response",
        "reviewer_action_matrix",
        "reviewer_artifact_inventory",
    }.issubset(scope_roles["medical"])
    assert {
        "selected_archive_manifest",
        "selected_build_receipt",
        "build_dependency_manifest",
        "root_reader_output",
        "selected_reader_output",
    }.issubset(scope_roles["display"])

    publication = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
    )["generation_manifest"]
    publication_roles = {
        scope["review_lane"]: {item["role"] for item in scope["reviewed_members"]}
        for scope in publication["review_scopes"]
    }
    selected_roles = {
        "selected_archive_manifest",
        "selected_build_receipt",
        "build_dependency_manifest",
        "root_reader_output",
        "selected_reader_output",
    }
    assert selected_roles.issubset(publication_roles["publication"])
    assert selected_roles.issubset(publication_roles["exact_byte_package"])
