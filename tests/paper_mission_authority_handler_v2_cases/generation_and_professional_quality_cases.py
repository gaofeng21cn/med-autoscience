from __future__ import annotations

from .shared import *

def test_generation_manifest_schema_enforces_binding_scope(
    authority_records: Any,
) -> None:
    validator = _schema_validator("mas-evidence-generation-manifest.schema.json")
    analysis = authority_records.candidate_request(manifest_version=2)[
        "generation_manifest"
    ]
    manuscript = authority_records.paper_request()["generation_manifest"]

    invalid_analysis = deepcopy(analysis)
    invalid_analysis["selected_build_binding"] = deepcopy(
        manuscript["selected_build_binding"]
    )
    invalid_analysis["reviewer_response_sync"] = deepcopy(
        manuscript["reviewer_response_sync"]
    )
    assert list(validator.iter_errors(invalid_analysis))

    invalid_analysis_artifact = deepcopy(analysis)
    reviewer_artifact = deepcopy(
        next(
            artifact
            for artifact in manuscript["artifacts"]
            if artifact["role"] == "reviewer_response"
        )
    )
    invalid_analysis_artifact["artifacts"].append(reviewer_artifact)
    assert list(validator.iter_errors(invalid_analysis_artifact))

    invalid_analysis_first_draft = deepcopy(analysis)
    invalid_analysis_first_draft["first_draft_quality_application"] = deepcopy(
        manuscript["first_draft_quality_application"]
    )
    assert list(validator.iter_errors(invalid_analysis_first_draft))

    invalid_manuscript = deepcopy(manuscript)
    invalid_manuscript["clinical_analysis_identity_admission"] = deepcopy(
        analysis["clinical_analysis_identity_admission"]
    )
    assert list(validator.iter_errors(invalid_manuscript))

def test_current_satisfied_first_draft_candidate_rejects_zero_byte_exact_ref(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request()
    application = request["generation_manifest"]["first_draft_quality_application"]
    candidate = application["candidate_refs"][
        "medical_initial_draft_preflight_candidate_ref"
    ]
    assert application["candidate_dispositions"][
        "medical_initial_draft_preflight_candidate_ref"
    ]["status"] == "satisfied"
    candidate["size_bytes"] = 0

    schema_errors = list(
        _schema_validator(
            "mas-evidence-generation-manifest.schema.json"
        ).iter_errors(request["generation_manifest"])
    )
    assert schema_errors

    result = _evaluate(request)
    assert result["status"] == "invalid_host_input"
    assert "size_bytes must be greater than zero" in result["error"]["detail"]


@pytest.mark.parametrize(
    ("validation_design", "expects_transportability"),
    [
        ("internal_external", False),
        ("external_validation", True),
    ],
)
def test_validation_design_routes_transportability_only_for_true_external_validation(
    authority_records: Any,
    validation_design: str,
    expects_transportability: bool,
) -> None:
    request = authority_records.paper_request(validation_design=validation_design)
    application = request["generation_manifest"]["first_draft_quality_application"]
    skill_ids = {
        item["skill_id"]
        for item in request["generation_manifest"]["professional_skill_invocations"]
    }

    assert (
        application["candidate_refs"]["external_transportability_ref"] is not None
    ) is expects_transportability
    assert (
        application["candidate_dispositions"]["external_transportability_ref"][
            "status"
        ]
        == "satisfied"
    ) is expects_transportability
    assert (
        "medical-risk-model-transportability-reviewer" in skill_ids
    ) is expects_transportability
    assert _evaluate(request)["status"] == "owner_receipt"


def test_non_clinical_other_manuscript_can_explicitly_dispose_data_freeze(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request(
        paper_type="other",
        validation_design="not_applicable",
        reports_fixed_horizon_risk=False,
        competing_risk_relevant=False,
        reports_decision_curve_analysis=False,
        uses_clinical_or_registry_data=False,
    )
    application = request["generation_manifest"]["first_draft_quality_application"]

    assert application["candidate_refs"][
        "clinical_analysis_input_identity_ref"
    ] is None
    assert application["candidate_dispositions"][
        "clinical_analysis_input_identity_ref"
    ]["status"] == "not_applicable_with_reason"
    assert "medical-data-freeze-and-analysis-readiness-reviewer" not in {
        item["skill_id"]
        for item in request["generation_manifest"]["professional_skill_invocations"]
    }
    assert _evaluate(request)["status"] == "owner_receipt"


def test_legacy_first_draft_application_is_readable_but_cannot_claim_current_quality(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request(
        first_draft_application_schema_version=1
    )

    result = _evaluate(request)

    route_back = _assert_progress_debt(
        result, "first_draft_candidate_dispositions_missing"
    )
    assert route_back["next_owner"] == "baseline_and_evidence_setup"
    assert request["generation_manifest"]["first_draft_quality_application"][
        "schema_version"
    ] == 1


@pytest.mark.parametrize(
    ("overrides", "expected_owner", "expected_reason"),
    [
        (
            {
                "medical_initial_draft_preflight_candidate_ref": {
                    "status": "route_back_required",
                    "earliest_route_back_owner": "manuscript_authoring",
                    "reason_codes": ["preflight_story_contract_unresolved"],
                    "unresolved_items": ["story-contract"],
                    "not_applicable_reason": None,
                }
            },
            "manuscript_authoring",
            "preflight_story_contract_unresolved",
        ),
        (
            {
                "author_stance_integrity_ref": {
                    "status": "route_back_required",
                    "earliest_route_back_owner": "manuscript_authoring",
                    "reason_codes": ["author_stance_integrity_unresolved"],
                    "unresolved_items": ["author-stated-objective-facts"],
                    "not_applicable_reason": None,
                }
            },
            "manuscript_authoring",
            "author_stance_integrity_unresolved",
        ),
        (
            {
                "medical_initial_draft_preflight_candidate_ref": {
                    "status": "route_back_required",
                    "earliest_route_back_owner": "manuscript_authoring",
                    "reason_codes": ["preflight_story_contract_unresolved"],
                    "unresolved_items": ["story-contract"],
                    "not_applicable_reason": None,
                },
                "model_complexity_sparse_event_ref": {
                    "status": "route_back_required",
                    "earliest_route_back_owner": "bounded_analysis_campaign",
                    "reason_codes": ["sparse_event_model_adequacy_unresolved"],
                    "unresolved_items": ["model-adequacy"],
                    "not_applicable_reason": None,
                },
            },
            "bounded_analysis_campaign",
            "sparse_event_model_adequacy_unresolved",
        ),
        (
            {
                "medical_initial_draft_preflight_candidate_ref": {
                    "status": "route_back_required",
                    "earliest_route_back_owner": "manuscript_authoring",
                    "reason_codes": ["preflight_story_contract_unresolved"],
                    "unresolved_items": ["story-contract"],
                    "not_applicable_reason": None,
                },
                "model_complexity_sparse_event_ref": {
                    "status": "route_back_required",
                    "earliest_route_back_owner": "bounded_analysis_campaign",
                    "reason_codes": ["sparse_event_model_adequacy_unresolved"],
                    "unresolved_items": ["model-adequacy"],
                    "not_applicable_reason": None,
                },
                "citation_source_coverage_ref": {
                    "status": "route_back_required",
                    "earliest_route_back_owner": "baseline_and_evidence_setup",
                    "reason_codes": ["citation_source_identity_unresolved"],
                    "unresolved_items": ["citation-source"],
                    "not_applicable_reason": None,
                },
            },
            "baseline_and_evidence_setup",
            "citation_source_identity_unresolved",
        ),
    ],
)
def test_first_draft_dispositions_route_to_the_earliest_canonical_owner(
    authority_records: Any,
    overrides: dict[str, dict[str, Any]],
    expected_owner: str,
    expected_reason: str,
) -> None:
    request = authority_records.paper_request(disposition_overrides=overrides)
    application = request["generation_manifest"]["first_draft_quality_application"]
    assert all(
        application["candidate_refs"][field] is not None for field in overrides
    )

    result = _evaluate(request)

    route_back = _assert_progress_debt(result, expected_reason)
    assert route_back["next_owner"] == expected_owner


def test_first_draft_routes_to_review_after_earlier_tiers_are_closed(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request(
        disposition_overrides={
            "medical_initial_draft_preflight_candidate_ref": {
                "status": "route_back_required",
                "earliest_route_back_owner": "review_and_quality_gate",
                "reason_codes": ["independent_first_draft_review_unresolved"],
                "unresolved_items": ["review-lane"],
                "not_applicable_reason": None,
            }
        }
    )
    dispositions = request["generation_manifest"][
        "first_draft_quality_application"
    ]["candidate_dispositions"]
    assert {
        item["earliest_route_back_owner"]
        for item in dispositions.values()
        if item["status"] == "route_back_required"
    } == {"review_and_quality_gate"}

    result = _evaluate(request)

    route_back = _assert_progress_debt(
        result, "independent_first_draft_review_unresolved"
    )
    assert route_back["next_owner"] == "review_and_quality_gate"


@pytest.mark.parametrize(
    ("earlier_field", "earlier_owner", "earlier_reason"),
    [
        (
            "citation_source_coverage_ref",
            "baseline_and_evidence_setup",
            "citation_source_identity_unresolved",
        ),
        (
            "model_complexity_sparse_event_ref",
            "bounded_analysis_campaign",
            "sparse_event_model_adequacy_unresolved",
        ),
        (
            "claim_guardrail_ref",
            "manuscript_authoring",
            "claim_guardrail_unresolved",
        ),
    ],
)
def test_first_draft_review_route_never_preempts_an_earlier_unresolved_tier(
    authority_records: Any,
    earlier_field: str,
    earlier_owner: str,
    earlier_reason: str,
) -> None:
    request = authority_records.paper_request(
        disposition_overrides={
            "medical_initial_draft_preflight_candidate_ref": {
                "status": "route_back_required",
                "earliest_route_back_owner": "review_and_quality_gate",
                "reason_codes": ["independent_first_draft_review_unresolved"],
                "unresolved_items": ["review-lane"],
                "not_applicable_reason": None,
            },
            earlier_field: {
                "status": "route_back_required",
                "earliest_route_back_owner": earlier_owner,
                "reason_codes": [earlier_reason],
                "unresolved_items": [earlier_field],
                "not_applicable_reason": None,
            },
        }
    )

    result = _evaluate(request)

    route_back = _assert_progress_debt(result, earlier_reason)
    assert route_back["next_owner"] == earlier_owner


def test_tampered_exact_professional_receipt_fails_closed(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request()
    invocation = next(
        item
        for item in request["generation_manifest"]["professional_skill_invocations"]
        if item["skill_id"] == "medical-display-qc"
    )
    invocation["receipt_ref"]["sha256"] = authority_records.digest(
        "tampered-scholar-receipt"
    )

    result = _evaluate(request)

    assert result["status"] == "invalid_host_input"
    assert "receipt_ref does not bind the Scholar v2 semantic receipt bytes" in result[
        "error"
    ]["detail"]


def test_selected_build_scholar_v2_semantic_bindings_are_exact_and_complete(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request()
    manifest = request["generation_manifest"]
    bindings = manifest["first_draft_quality_application"][
        "scholar_v2_semantic_policy_bindings"
    ]

    assert {item["skill_id"] for item in bindings} == {
        "medical-manuscript-writing",
        "medical-statistical-review",
        "medical-reference-integrity-auditor",
        "medical-display-qc",
    }
    assert _evaluate(request)["status"] == "owner_receipt"

    missing_binding = deepcopy(request)
    missing_binding["generation_manifest"]["first_draft_quality_application"][
        "scholar_v2_semantic_policy_bindings"
    ].pop()
    result = _evaluate(missing_binding)
    assert result["status"] == "invalid_host_input"
    assert "exactly one current binding for each applicable" in result["error"][
        "detail"
    ]

    duplicate_invocation = deepcopy(request)
    duplicate_invocation["generation_manifest"][
        "professional_skill_invocations"
    ].append(
        deepcopy(
            duplicate_invocation["generation_manifest"][
                "professional_skill_invocations"
            ][0]
        )
    )
    result = _evaluate(duplicate_invocation)
    assert result["status"] == "invalid_host_input"
    assert "duplicate target/skill receipts" in result["error"]["detail"]


def test_selected_build_rejects_legacy_or_orphan_scholar_v2_invocation(
    authority_records: Any,
) -> None:
    legacy_invocation = authority_records.paper_request()
    invocation = next(
        item
        for item in legacy_invocation["generation_manifest"][
            "professional_skill_invocations"
        ]
        if item["skill_id"] == "medical-manuscript-writing"
    )
    invocation["schema_version"] = 1
    for field in (
        "invocation_ref",
        "receipt_ref",
        "input_artifact_bindings",
        "semantic_policy_id",
        "semantic_validator_id",
        "semantic_policy_ref",
        "semantic_candidate_ref",
    ):
        del invocation[field]
    authority_records.refresh_paper_manifest_identity(legacy_invocation)
    result = _evaluate(legacy_invocation)
    assert result["status"] == "invalid_host_input"
    assert "requires a v2 professional invocation" in result["error"]["detail"]

    orphan_binding = authority_records.paper_request()
    binding = orphan_binding["generation_manifest"][
        "first_draft_quality_application"
    ]["scholar_v2_semantic_policy_bindings"][0]
    binding["invocation_ref"] = authority_records.exact_ref(
        "mas_professional_skill_invocation", "orphan-invocation"
    )
    result = _evaluate(orphan_binding)
    assert result["status"] == "invalid_host_input"
    assert "does not match exact invocation and receipt refs" in result["error"][
        "detail"
    ]


@pytest.mark.parametrize(
    ("tamper", "expected_detail"),
    [
        ("policy_ref", "receipt_ref does not bind the Scholar v2 semantic receipt bytes"),
        ("candidate_ref", "must bind the current first-draft candidate artifact bytes"),
        ("consumed_rule", "must consume the exact semantic policy and validator"),
    ],
)
def test_selected_build_rejects_tampered_scholar_v2_semantics(
    authority_records: Any,
    tamper: str,
    expected_detail: str,
) -> None:
    request = authority_records.paper_request()
    application = request["generation_manifest"]["first_draft_quality_application"]
    binding = next(
        item
        for item in application["scholar_v2_semantic_policy_bindings"]
        if item["skill_id"] == "medical-manuscript-writing"
    )
    invocation = next(
        item
        for item in request["generation_manifest"]["professional_skill_invocations"]
        if item["skill_id"] == "medical-manuscript-writing"
    )
    if tamper == "policy_ref":
        invocation["semantic_policy_ref"] = authority_records.exact_ref(
            "scholarskills_semantic_policy", "tampered-policy"
        )
    elif tamper == "candidate_ref":
        binding["candidate_ref"] = authority_records.mas_artifact_ref(
            next(
                item
                for item in request["generation_manifest"]["artifacts"]
                if item["role"] == "claim_guardrail"
            )
        )
    else:
        invocation["consumed_rule_refs"].remove(
            "validator:validate_medical_initial_draft_preflight_candidate_v3"
        )

    result = _evaluate(request)

    assert result["status"] == "invalid_host_input"
    assert expected_detail in result["error"]["detail"]


def test_pdf_byte_change_invalidates_display_review_scope_and_skill_receipt(
    authority_records: Any,
) -> None:
    origin = authority_records.paper_request(
        artifact_sha_overrides={"pdf": authority_records.digest("paper-pdf-v1")}
    )
    current = authority_records.paper_request(
        artifact_sha_overrides={"pdf": authority_records.digest("paper-pdf-v2")}
    )
    origin_display = next(
        item
        for item in origin["generation_manifest"]["review_scopes"]
        if item["review_lane"] == "display"
    )
    current_display = next(
        item
        for item in current["generation_manifest"]["review_scopes"]
        if item["review_lane"] == "display"
    )
    assert "pdf" in {item["role"] for item in current_display["reviewed_members"]}
    assert origin_display["review_scope_sha256"] == current_display[
        "review_scope_sha256"
    ]
    origin_receipt = next(
        item["receipt_ref"]
        for item in origin["generation_manifest"]["professional_skill_invocations"]
        if item["skill_id"] == "medical-display-qc"
    )
    current_receipt = next(
        item["receipt_ref"]
        for item in current["generation_manifest"]["professional_skill_invocations"]
        if item["skill_id"] == "medical-display-qc"
    )
    assert origin_receipt != current_receipt

    pdf_member = next(
        item
        for item in current["generation_manifest"]["artifacts"]
        if item["role"] == "pdf"
    )
    _authorize_reused_lane(
        current,
        origin,
        "display",
        authority_records,
        invalidating_changes=[
            _epistemic_change(
                authority_records,
                node_ref=pdf_member["member_id"],
                change_class="visual_content",
            )
        ],
    )
    result = _evaluate(current)
    _assert_progress_debt(
        result, "first_draft_cross_domain_pre_review_missing_or_stale"
    )
    assert result["route_back"]["affected_review_lanes"][0][
        "review_lane"
    ] == "display"


def test_missing_professional_figure_skill_receipts_are_progress_first_quality_debt(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request(
        omit_professional_skill_ids=(
            "medical-figure-design",
            "medical-figure-style",
        )
    )

    result = _evaluate(request)

    route_back = _assert_progress_debt(
        result, "professional_figure_skill_consumption_evidence_missing"
    )
    assert route_back["next_owner"] == "mission_executor"
    assert (
        result["quality_debt"][
            "blocks_quality_publication_export_and_submission_claims"
        ]
        is True
    )
    _output_validator().validate(result)


def test_missing_final_style_receipt_is_targeted_quality_debt(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request(
        omit_professional_skill_ids=("medical-figure-style",)
    )

    result = _evaluate(request)

    _assert_progress_debt(result, "professional_figure_style_consumption_missing")
    _output_validator().validate(result)


def test_assembled_panels_require_composer_receipt_without_blocking_liveness(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request(
        professional_figure_composition_mode="assembled_panels",
        omit_professional_skill_ids=("medical-figure-composer",),
    )

    result = _evaluate(request)

    _assert_progress_debt(result, "professional_figure_composer_consumption_missing")
    _output_validator().validate(result)


def test_stale_professional_skill_output_binding_is_quality_debt(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request()
    figure_invocation = next(
        item
        for item in request["generation_manifest"]["professional_skill_invocations"]
        if item["skill_id"] == "medical-figure-design"
    )
    figure_invocation["output_artifact_bindings"][0]["sha256"] = (
        authority_records.digest("stale-figure-output")
    )
    authority_records.refresh_paper_manifest_identity(request)

    result = _evaluate(request)

    _assert_progress_debt(result, "professional_figure_skill_output_binding_stale")
    _output_validator().validate(result)


def test_finalize_routes_back_when_professional_figure_receipts_are_missing(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        omit_professional_skill_ids=(
            "medical-figure-design",
            "medical-figure-style",
        ),
    )

    result = _evaluate(request)

    assert result["status"] == "route_back"
    assert result["stage_outcome"]["stage_transition_allowed"] is False
    assert result["route_back"]["reason_code"] == (
        "professional_figure_skill_consumption_evidence_missing"
    )
    _output_validator().validate(result)


def test_selected_build_missing_manuscript_writing_skill_fails_closed(
    authority_records: Any,
) -> None:
    authoring = authority_records.paper_request(
        omit_professional_skill_ids=("medical-manuscript-writing",)
    )
    result = _evaluate(authoring)
    assert result["status"] == "invalid_host_input"
    assert "requires one exact professional invocation" in result["error"]["detail"]

    finalize = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        omit_professional_skill_ids=("medical-manuscript-writing",),
    )
    result = _evaluate(finalize)
    assert result["status"] == "invalid_host_input"
    assert "requires one exact professional invocation" in result["error"]["detail"]


@pytest.mark.parametrize(
    ("skill_id", "reason_code"),
    [
        (
            "medical-statistical-review",
            "professional_statistical_review_consumption_missing",
        ),
        (
            "medical-table-design",
            "professional_table_design_consumption_missing",
        ),
    ],
)
def test_first_draft_requires_specialists_for_present_artifact_roles(
    authority_records: Any,
    skill_id: str,
    reason_code: str,
) -> None:
    request = authority_records.paper_request(
        omit_professional_skill_ids=(skill_id,),
    )

    result = _evaluate(request)

    if skill_id == "medical-statistical-review":
        assert result["status"] == "invalid_host_input"
        assert "requires one exact professional invocation" in result["error"][
            "detail"
        ]
    else:
        _assert_progress_debt(result, reason_code)


def test_table_skill_receipt_without_quality_application_is_progress_first_debt(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request()
    invocation = next(
        item
        for item in request["generation_manifest"]["professional_skill_invocations"]
        if item["skill_id"] == "medical-table-design"
    )
    del invocation["table_quality_application"]
    authority_records.refresh_paper_manifest_identity(request)

    result = _evaluate(request)

    _assert_progress_debt(result, "professional_table_quality_application_missing")


def test_overloaded_main_table_cannot_pass_finalize_with_skill_receipt(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
    )
    invocation = next(
        item
        for item in request["generation_manifest"]["professional_skill_invocations"]
        if item["skill_id"] == "medical-table-design"
    )
    table = invocation["table_quality_application"]["main_tables"][0]
    table.update(
        {
            "row_count": 23,
            "column_count": 9,
            "body_word_count": 900,
            "max_cell_word_count": 36,
            "footnote_word_count": 120,
            "supplementary_detail_refs": [],
            "final_embedding_status": "pending",
            "final_embedding_page_span": 2,
        }
    )
    authority_records.refresh_paper_manifest_identity(request)

    result = _evaluate(request)

    route_back = _assert_finalize_route_back(
        result,
        "professional_main_table_information_budget_exceeded",
    )
    assert route_back["next_owner"] == "mission_executor"


def test_overloaded_main_table_is_progress_first_debt_during_authoring(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request()
    invocation = next(
        item
        for item in request["generation_manifest"]["professional_skill_invocations"]
        if item["skill_id"] == "medical-table-design"
    )
    table = invocation["table_quality_application"]["main_tables"][0]
    table.update(
        {
            "row_count": 23,
            "column_count": 9,
            "body_word_count": 900,
            "max_cell_word_count": 36,
            "footnote_word_count": 120,
            "supplementary_detail_refs": [],
            "final_embedding_status": "pending",
            "final_embedding_page_span": 2,
        }
    )
    authority_records.refresh_paper_manifest_identity(request)

    result = _evaluate(request)

    _assert_progress_debt(
        result,
        "professional_main_table_information_budget_exceeded",
    )


def test_readable_documented_main_table_exception_is_not_template_blocked(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request()
    invocation = next(
        item
        for item in request["generation_manifest"]["professional_skill_invocations"]
        if item["skill_id"] == "medical-table-design"
    )
    table = invocation["table_quality_application"]["main_tables"][0]
    table.update(
        {
            "row_count": 16,
            "budget_status": "documented_exception",
            "exception_reason": (
                "The target journal permits this readable baseline table."
            ),
        }
    )
    authority_records.refresh_paper_manifest_identity(request)

    result = _evaluate(request)

    reason_codes = (result.get("quality_debt") or {}).get("reason_codes", [])
    assert not {
        "professional_main_table_information_budget_exceeded",
        "professional_main_table_supplementary_route_missing",
        "professional_main_table_final_embedding_incomplete",
    } & set(reason_codes)


def test_main_table_standalone_notes_heading_is_quality_debt(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request()
    invocation = next(
        item
        for item in request["generation_manifest"]["professional_skill_invocations"]
        if item["skill_id"] == "medical-table-design"
    )
    table = invocation["table_quality_application"]["main_tables"][0]
    table["standalone_notes_heading_present"] = True
    authority_records.refresh_paper_manifest_identity(request)

    result = _evaluate(request)

    _assert_progress_debt(result, "professional_main_table_notes_heading_present")


def test_compact_main_table_with_supplementary_detail_passes_table_quality_gate(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request()

    result = _evaluate(request)

    assert (result.get("quality_debt") or {}).get("reason_codes", []) == []


def test_submission_prep_is_progress_first_debt_until_finalize(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request(
        scope="publication_generation",
        omit_professional_skill_ids=("medical-submission-prep",),
    )
    result = _evaluate(request)
    _assert_progress_debt(
        result,
        "professional_submission_prep_consumption_missing",
    )

    finalize = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        omit_professional_skill_ids=("medical-submission-prep",),
    )
    result = _evaluate(finalize)
    _assert_finalize_route_back(
        result,
        "professional_submission_prep_consumption_missing",
    )


def test_submission_prep_receipt_must_cover_supplement_and_package_bytes(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request(scope="publication_generation")
    invocation = next(
        item
        for item in request["generation_manifest"]["professional_skill_invocations"]
        if item["skill_id"] == "medical-submission-prep"
    )
    invocation["output_artifact_bindings"] = [
        item
        for item in invocation["output_artifact_bindings"]
        if item["role"] != "supplementary_output"
    ]
    authority_records.refresh_paper_manifest_identity(request)

    result = _evaluate(request)

    _assert_progress_debt(
        result,
        "professional_submission_prep_output_coverage_incomplete",
    )


def test_host_cannot_turn_manuscript_skill_candidate_into_authority(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request()
    invocation = next(
        item
        for item in request["generation_manifest"]["professional_skill_invocations"]
        if item["skill_id"] == "medical-manuscript-writing"
    )
    invocation["authority"] = True

    result = _evaluate(request)

    assert result["status"] == "invalid_host_input"
    assert "cannot grant authority" in result["error"]["detail"]


def test_first_draft_cross_domain_pre_review_missing_is_progress_first_debt(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request(stage_id="review_and_quality_gate")
    request["generation_manifest"]["independent_review_receipts"] = [
        wrapper
        for wrapper in request["generation_manifest"]["independent_review_receipts"]
        if wrapper["receipt"]["review_lane"] != "medical"
    ]

    result = _evaluate(request)

    assert result["status"] == "completed_with_quality_debt"
    assert result["stage_outcome"]["stage_transition_allowed"] is True
    assert (
        "first_draft_cross_domain_pre_review_missing_or_stale"
        in result["quality_debt"]["reason_codes"]
    )


def test_finalize_rejects_stale_exact_byte_package_after_package_change(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
    )
    package_member = next(
        item
        for item in request["generation_manifest"]["artifacts"]
        if item["role"] == "final_zip_member"
    )
    package_member["sha256"] = authority_records.digest("dm003-new-package-bytes")
    authority_records.refresh_paper_manifest_identity(request)

    result = _evaluate(request)

    assert result["status"] == "route_back"
    assert result["stage_outcome"]["stage_transition_allowed"] is False
    assert result["route_back"]["reason_code"] in {
        "professional_manuscript_skill_output_binding_stale",
        "independent_review_receipt_not_current",
        "review_currentness_scope_mismatch",
    }


def test_invalid_present_professional_skill_package_identity_fails_closed(
    authority_records: Any,
) -> None:
    manifest, _ = authority_records.generation_manifest(
        "manuscript_generation", schema_version=2
    )
    manifest["professional_skill_invocations"][0]["package_id"] = "forged-pack"
    core = {
        key: deepcopy(manifest[key])
        for key in (
            "surface_kind",
            "schema_version",
            "generation_id",
            "manifest_scope",
            "artifacts",
            "review_scopes",
            "professional_skill_invocations",
        )
    }
    manifest["generation_manifest_sha256"] = authority_records.fingerprint(core)

    with pytest.raises(ValueError, match="package_id must be mas-scholar-skills"):
        normalize_generation_manifest(manifest)
