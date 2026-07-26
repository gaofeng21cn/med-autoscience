from __future__ import annotations

from .shared import *

def test_missing_revision_consumption_binding_is_progress_first_quality_debt(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request()
    request.pop("revision_consumption")

    result = _evaluate(request)

    route_back = _assert_progress_debt(result, "revision_consumption_binding_required")
    assert route_back["next_owner"] == "mas_revision_consumption_owner"
    _output_validator().validate(result)


def test_canonical_manuscript_contract_rejects_stale_package_source_clobber() -> None:
    stage_pack = json.loads(
        (ROOT / "contracts/mas-paper-study-stage-pack.json").read_text(
            encoding="utf-8"
        )
    )
    contract = stage_pack["reviewer_revision_default_mechanism"][
        "canonical_manuscript_currentness_contract"
    ]

    assert contract["canonical_editable_source"] == {
        "root": "workspace:manuscript/",
        "role": "authoring_input",
        "package_publish_output": False,
        "may_be_overwritten_by_shallow_publish": False,
    }
    projection = contract["delivery_projection"]
    assert projection["manuscript_source_copy_role"] == "source_lineage_copy"
    assert projection["source_lineage_copy_is_editable_source"] is False
    assert projection["publish_direction"] == (
        "canonical_editable_source_to_delivery_projection_only"
    )
    assert projection["shallow_collision_policy"] == (
        "reject_if_target_is_canonical_editable_source"
    )
    assert projection["document_identity_projection"] == {
        "canonical_title_source": "current_canonical_editable_source",
        "visible_title_derived_from_canonical_source": True,
        "export_metadata_title_when_present_derived_from_same_title": True,
        "hardcoded_or_secondary_title_constant_allowed": False,
        "title_mismatch_disposition": "reject_finalize_or_publication_handoff",
    }
    assert projection["handoff_selection"] == {
        "selector_source": "current_published_delivery_manifest",
        "role_based_resolution_required": True,
        "direct_or_legacy_path_selection_allowed": False,
        "required_checks": [
            "selected_generation_matches_current_delivery",
            "selected_path_is_declared_by_current_projection_plan",
            "selected_bytes_match_current_manifest_record",
        ],
        "selection_receipt_required": True,
        "selection_failure_disposition": "reject_handoff",
    }

    currentness = contract["revision_currentness"]
    assert currentness["required_inputs"] == {
        "current_revision_inventory": (
            "mas_revision_consumption_binding."
            "current_accepted_or_active_revision_intake_refs"
        ),
        "current_revision_inventory_source": "workspace_revision_intake_registry",
        "generation_consumption": (
            "mas_revision_consumption_binding.consumption_receipt."
            "consumed_revision_refs"
        ),
    }
    assert currentness["current_delivery_predicate"] == (
        "every_current_accepted_or_active_revision_ref_is_consumed_by_current_generation"
    )
    assert currentness[
        "latest_accepted_or_active_revision_must_be_consumed_by_current_generation"
    ] is True
    assert currentness["package_internal_consistency_is_current_delivery_proof"] is False
    assert currentness["ordinary_authoring_or_render_when_unconsumed"] == (
        "completed_with_quality_debt"
    )
    assert currentness["ordinary_stage_transition_allowed"] is True
    assert currentness["finalize_or_publication_handoff_when_unconsumed"] == (
        "route_back"
    )
    assert currentness["milestone_delivered_claim_allowed"] is False
    assert currentness["current_revision_delivered_claim_allowed"] is False
    assert currentness["publication_authority"] is False
    assert currentness["submission_authority"] is False

    assert contract["selective_invalidation"][
        "package_or_layout_only_delta_invalidates_content_review"
    ] is False
    assert contract["counterexample_outcomes"] == {
        "internally_consistent_old_package_with_newer_unconsumed_revision": (
            "not_current_delivery"
        ),
        "delivery_source_lineage_copy_would_overwrite_newer_canonical_source": (
            "reject_publish"
        ),
        "current_visible_title_with_stale_export_metadata_title": (
            "reject_finalize_or_publication_handoff"
        ),
        "existing_stale_legacy_pdf_selected_by_direct_path": "reject_handoff",
    }


def test_internally_consistent_package_cannot_finalize_without_revision_currentness(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
    )
    request["revision_consumption"][
        "current_accepted_or_active_revision_intake_refs"
    ] = [authority_records.exact_ref("opl_revision_intake", "newer-revision")]

    result = _evaluate(request)

    route_back = _assert_finalize_route_back(
        result, "latest_accepted_or_active_revision_not_consumed"
    )
    assert route_back["next_owner"] == "mas_revision_consumption_owner"
    assert result["stage_outcome"]["publication_or_submission_ready"] is False
    assert result["owner_receipt"] is None
    assert result["quality_debt"] is None
    _output_validator().validate(result)


def test_missing_current_revision_inventory_is_progress_first_quality_debt(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request()
    request["revision_consumption"].pop(
        "current_accepted_or_active_revision_intake_refs"
    )

    result = _evaluate(request)

    route_back = _assert_progress_debt(
        result, "revision_currentness_inventory_required"
    )
    assert route_back["next_owner"] == "mas_revision_consumption_owner"
    _output_validator().validate(result)


def test_explicit_null_revision_consumption_binding_is_invalid(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request()
    request["revision_consumption"] = None

    result = _evaluate(request)

    assert result["status"] == "invalid_host_input"
    assert "must be an object when supplied" in result["error"]["detail"]


def test_consumed_revision_closure_is_projected_into_owner_receipt(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request()
    authority_records.bind_revision_consumption(
        request,
        finding_statuses={"OPL-REV-001": "closed", "OPL-REV-002": "closed"},
        revision_intake_names=("reviewer-round-1", "reviewer-round-2"),
    )

    result = _evaluate(request)

    assert result["status"] == "owner_receipt"
    projection = result["owner_receipt"]["revision_consumption"]
    receipt = request["revision_consumption"]["consumption_receipt"]
    assert projection == {
        "surface_kind": "mas_revision_consumption_owner_projection",
        "schema_version": 1,
        "consumption_receipt_ref": request["revision_consumption"][
            "consumption_receipt_ref"
        ],
        "applicability": "revision_consumed",
        "revision_intake_refs": receipt["revision_intake_refs"],
        "opl_review_receipt_ref": receipt["opl_review_receipt_ref"],
        "opl_finding_lineage": receipt["opl_finding_lineage"],
        "finding_closures": receipt["finding_closures"],
        "consumed_revision_refs": receipt["consumed_revision_refs"],
        "authority_boundary": {
            "receipt_can_authorize_review_verdict": False,
            "receipt_can_authorize_owner_receipt": False,
            "receipt_can_authorize_publication": False,
            "receipt_can_authorize_submission": False,
            "receipt_can_create_typed_blocker": False,
        },
    }
    validator = _output_validator()
    validator.validate(result)
    forged_open_projection = deepcopy(result)
    forged_open_projection["owner_receipt"]["revision_consumption"]["finding_closures"][
        0
    ]["status"] = "partially_closed"
    assert list(validator.iter_errors(forged_open_projection))


def test_partial_revision_finding_closure_is_quality_debt(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request()
    authority_records.bind_revision_consumption(
        request,
        finding_statuses={
            "OPL-REV-001": "closed",
            "OPL-REV-002": "partially_closed",
        },
    )

    result = _evaluate(request)

    route_back = _assert_progress_debt(result, "revision_finding_closure_incomplete")
    assert route_back["next_owner"] == "mas_revision_consumption_owner"


def test_revision_consumption_rejects_incomplete_or_unbound_exact_refs(
    authority_records: Any,
) -> None:
    incomplete = authority_records.paper_request()
    authority_records.bind_revision_consumption(incomplete)
    incomplete_receipt = incomplete["revision_consumption"]["consumption_receipt"]
    incomplete_receipt["consumed_revision_refs"].pop()
    authority_records.reseal_revision_consumption(incomplete)
    result = _evaluate(incomplete)
    assert result["status"] == "invalid_host_input"
    assert "must exactly equal revision intake" in result["error"]["detail"]

    missing_lineage = authority_records.paper_request()
    authority_records.bind_revision_consumption(missing_lineage)
    missing_receipt = missing_lineage["revision_consumption"]["consumption_receipt"]
    missing_receipt["opl_finding_lineage"] = None
    missing_receipt["finding_closures"] = []
    authority_records.reseal_revision_consumption(missing_lineage)
    result = _evaluate(missing_lineage)
    assert result["status"] == "invalid_host_input"
    assert "opl_finding_lineage are required" in result["error"]["detail"]

    missing_closure_hash = authority_records.paper_request()
    authority_records.bind_revision_consumption(missing_closure_hash)
    missing_hash_receipt = missing_closure_hash["revision_consumption"][
        "consumption_receipt"
    ]
    missing_hash_receipt["opl_finding_lineage"]["repair_map_sha256"] = None
    authority_records.reseal_revision_consumption(missing_closure_hash)
    result = _evaluate(missing_closure_hash)
    assert result["status"] == "invalid_host_input"
    assert "requires repair_map_sha256" in result["error"]["detail"]


@pytest.mark.parametrize(
    ("field", "replacement", "detail"),
    [
        ("generation_id", "other-generation", "generation_id does not match"),
        (
            "producer_attempt_ref",
            {
                "kind": "opl_stage_attempt",
                "ref": "opl_stage_attempt://other-attempt",
                "sha256": "sha256:" + "1" * 64,
            },
            "producer_attempt_ref does not match",
        ),
        (
            "producer_output_ref",
            {
                "kind": "opl_action_output",
                "ref": "opl_action_output://other-output",
                "size_bytes": 321,
                "sha256": "sha256:" + "2" * 64,
            },
            "producer_output_ref does not match",
        ),
    ],
)
def test_revision_consumption_rejects_cross_record_identity_tampering(
    authority_records: Any,
    field: str,
    replacement: object,
    detail: str,
) -> None:
    request = authority_records.paper_request()
    authority_records.bind_revision_consumption(request)
    request["revision_consumption"]["consumption_receipt"][field] = replacement
    authority_records.reseal_revision_consumption(request)

    result = _evaluate(request)

    assert result["status"] == "invalid_host_input"
    assert detail in result["error"]["detail"]


def test_revision_consumption_rejects_receipt_ref_hash_tampering(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request()
    authority_records.bind_revision_consumption(request)
    request["revision_consumption"]["consumption_receipt_ref"]["sha256"] = (
        "sha256:" + "0" * 64
    )

    result = _evaluate(request)

    assert result["status"] == "invalid_host_input"
    assert "does not match canonical receipt bytes" in result["error"]["detail"]


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
    route_back = _assert_progress_debt(result, "independent_review_receipt_not_current")
    assert route_back["reason_code"] == "independent_review_receipt_not_current"

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
    table_binding = next(
        binding
        for invocation in stale["generation_manifest"]["professional_skill_invocations"]
        for binding in invocation["output_artifact_bindings"]
        if binding["member_id"] == table["member_id"]
    )
    table_binding["sha256"] = table["sha256"]
    authority_records.refresh_paper_manifest_identity(stale)
    result = _evaluate(stale)
    _assert_progress_debt(result, "independent_review_stale_after_canonical_change")

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
        wrapper["receipt"]["issued_generation_manifest_sha256"] = manifest[
            "generation_manifest_sha256"
        ]
        # Deliberately retain the old wrapper ref/hash to model metadata-only reuse.
    result = _evaluate(metadata_rewrite)
    assert result["status"] == "invalid_host_input"
    assert "identity/size/hash" in result["error"]["detail"]


def test_v2_review_scopes_are_mas_owned_generation_independent_domain_graphs(
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
        "member_id" not in item for item in transport["generation_bound_truth_members"]
    )
    first_scopes = {
        item["review_lane"]: item
        for item in first["generation_manifest"]["review_scopes"]
    }
    second_scopes = {
        item["review_lane"]: item
        for item in second["generation_manifest"]["review_scopes"]
    }
    for lane in {
        "medical",
        "statistical",
        "reference",
        "display",
        "publication",
        "exact_byte_package",
    }:
        assert (
            first_scopes[lane]["review_scope_sha256"]
            == second_scopes[lane]["review_scope_sha256"]
        )
        roles = {item["role"] for item in first_scopes[lane]["reviewed_members"]}
        assert "source_input_digest" not in roles
        assert "candidate_admission_receipt" not in roles
        epistemic_scope = first_scopes[lane]["epistemic_scope"]
        assert epistemic_scope["evidence_profile"] == "epistemic_provenance"
        assert epistemic_scope["trust_model"] == "trusted_local_workspace"
        assert epistemic_scope["authority_boundary"] == {
            "hash_is_locator_or_stale_hint_only": True,
            "hash_is_content_authority": False,
            "release_integrity_is_separate": True,
            "framework_can_issue_domain_verdict": False,
        }
    exact_roles = {
        item["role"]
        for item in first_scopes["exact_byte_package"]["reviewed_members"]
    }
    assert exact_roles == {
        "docx",
        "pdf",
        "supplementary_output",
        "final_zip_allowlist",
        "final_zip_member",
        "selected_archive_manifest",
        "selected_build_receipt",
        "build_dependency_manifest",
        "root_reader_output",
        "selected_reader_output",
    }
    assert exact_roles.isdisjoint(
        {
            "submission_status",
            "publication_evaluation",
            "next_action_envelope",
            "submission_projection_manifest",
        }
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
    assert [item["review_lane"] for item in built["review_scopes"]] == sorted(
        {
            "medical",
            "statistical",
            "reference",
            "display",
            "publication",
            "exact_byte_package",
        }
    )
    assert (
        normalize_generation_manifest(built)["generation_manifest_sha256"]
        == built["generation_manifest_sha256"]
    )

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


def test_v2_scope_locator_tracks_dependency_topology_not_member_bytes(
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
    for role in (
        "analysis_output",
        "canonical_manuscript",
        "reference_library",
        "render_environment_and_font_manifest",
        "final_zip_member",
        "submission_status",
    ):
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
        assert changed_scopes == baseline_scopes


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
            "figure_file": "workspace://study/figures/renamed-figure",
            "final_zip_member": "workspace://study/package/renamed-member",
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
    assert renamed_digests == baseline_digests
    for lane in {"display", "publication"}:
        assert replacement_digests[lane] != baseline_digests[lane]
    assert (
        replacement_digests["exact_byte_package"]
        == baseline_digests["exact_byte_package"]
    )
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
    reordered["review_authority"]["currentness_receipt"]["lane_currentness"].reverse()
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
    exact_scope["reviewed_members"][1]["member_id"] = exact_scope["reviewed_members"][
        0
    ]["member_id"]
    result = _evaluate(duplicate_review)
    assert result["status"] == "invalid_host_input"
    assert "duplicate member_id" in result["error"]["detail"]


def test_v2_layout_package_and_governance_deltas_preserve_content_verdicts(
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
            "render_environment_and_font_manifest": authority_records.digest(
                "changed-render-template-bytes"
            ),
            "final_zip_member": authority_records.digest(
                "changed-package-member-bytes"
            ),
            "submission_status": authority_records.digest(
                "changed-governance-status-bytes"
            ),
        },
    )
    ignored_changes = [
        _epistemic_change(
            authority_records,
            node_ref="mas-member:render_environment_and_font_manifest:primary",
            change_class="render_template",
            reason="outside_declared_evidence_graph",
        ),
        _epistemic_change(
            authority_records,
            node_ref="mas-member:final_zip_member:primary",
            change_class="package_composition",
            reason="outside_declared_evidence_graph",
        ),
        _epistemic_change(
            authority_records,
            node_ref="mas-member:submission_status:primary",
            change_class="governance_metadata",
            reason="outside_declared_evidence_graph",
        ),
    ]
    for lane in ("medical", "statistical", "reference"):
        _authorize_reused_lane(
            current,
            origin,
            lane,
            authority_records,
            ignored_changes=ignored_changes,
        )

    result = _evaluate(current)

    assert result["status"] == "owner_receipt"
    lane_states = {
        item["review_lane"]: item
        for item in current["review_authority"]["currentness_receipt"][
            "lane_currentness"
        ]
    }
    for lane in ("medical", "statistical", "reference"):
        assert lane_states[lane]["currentness_status"] == "reused_unchanged_scope"
        assert lane_states[lane]["epistemic_currentness"]["status"] == "current"
        assert len(lane_states[lane]["epistemic_currentness"]["ignored_changes"]) == 3


@pytest.mark.parametrize(
    ("role", "change_class", "affected_lanes"),
    [
        (
            "analysis_output",
            "analysis_result",
            ("medical", "statistical", "display"),
        ),
        (
            "canonical_manuscript",
            "claim",
            ("medical", "statistical", "reference", "display", "publication"),
        ),
        (
            "reference_library",
            "reference_source",
            ("reference", "publication"),
        ),
        (
            "render_environment_and_font_manifest",
            "render_template",
            ("display", "publication"),
        ),
        (
            "final_zip_member",
            "package_composition",
            ("publication", "exact_byte_package"),
        ),
    ],
)
def test_v2_semantic_changes_stale_only_declared_dependency_lanes(
    authority_records: Any,
    role: str,
    change_class: str,
    affected_lanes: tuple[str, ...],
) -> None:
    origin = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        generation_id=f"epistemic-origin-{role}",
    )
    current = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        generation_id=f"epistemic-current-{role}",
        artifact_sha_overrides={
            role: authority_records.digest(f"semantic-change:{role}")
        },
    )
    change = _epistemic_change(
        authority_records,
        node_ref=f"mas-member:{role}:primary",
        change_class=change_class,
    )
    ignored_change = {**change, "reason": "outside_declared_evidence_graph"}
    all_lanes = (
        "medical",
        "statistical",
        "reference",
        "display",
        "publication",
        "exact_byte_package",
    )
    for lane in all_lanes:
        _authorize_reused_lane(
            current,
            origin,
            lane,
            authority_records,
            invalidating_changes=[change] if lane in affected_lanes else None,
            ignored_changes=None if lane in affected_lanes else [ignored_change],
        )

    origin_locators = {
        item["review_lane"]: item["review_scope_sha256"]
        for item in origin["generation_manifest"]["review_scopes"]
    }
    current_locators = {
        item["review_lane"]: item["review_scope_sha256"]
        for item in current["generation_manifest"]["review_scopes"]
    }
    assert current_locators == origin_locators

    result = _evaluate(current)

    route_back = _assert_finalize_route_back(
        result, "independent_review_stale_after_epistemic_change"
    )
    assert [
        item["review_lane"] for item in route_back["affected_review_lanes"]
    ] == list(affected_lanes)
    assert {item["reason_code"] for item in route_back["affected_review_lanes"]} == {
        "independent_review_stale_after_epistemic_change"
    }


def test_v2_hash_only_locator_drift_preserves_review_currentness(
    authority_records: Any,
) -> None:
    origin = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        generation_id="locator-origin",
    )
    current = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
        generation_id="locator-current",
        artifact_ref_overrides={
            "analysis_output": "workspace://study/analysis/relocated-output"
        },
        artifact_sha_overrides={
            "analysis_output": authority_records.digest("relocated-output-bytes")
        },
    )
    ignored = _epistemic_change(
        authority_records,
        node_ref="mas-member:analysis_output:primary",
        change_class="locator_only",
        reason="locator_or_non_semantic_change_only",
    )
    for lane in ("medical", "statistical", "display"):
        _authorize_reused_lane(
            current,
            origin,
            lane,
            authority_records,
            ignored_changes=[ignored],
        )

    assert _evaluate(current)["status"] == "owner_receipt"
