from __future__ import annotations

from .shared import *

def test_v2_epistemic_currentness_is_required_and_bound_to_dependency_closure(
    authority_records: Any,
) -> None:
    missing = authority_records.paper_request()
    lane_state = missing["review_authority"]["currentness_receipt"][
        "lane_currentness"
    ][0]
    lane_state.pop("epistemic_currentness")
    authority_records.reseal_review_currentness(missing)

    result = _evaluate(missing)

    assert result["status"] == "invalid_host_input"
    assert "epistemic_currentness" in result["error"]["detail"]

    mismatched = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
    )
    lane_state = next(
        item
        for item in mismatched["review_authority"]["currentness_receipt"][
            "lane_currentness"
        ]
        if item["review_lane"] == "medical"
    )
    lane_state["epistemic_currentness"]["reviewed_dependency_refs"] = [
        "mas-member:canonical_manuscript:primary"
    ]
    authority_records.reseal_review_currentness(mismatched)

    result = _evaluate(mismatched)

    route_back = _assert_finalize_route_back(
        result, "epistemic_review_scope_binding_required"
    )
    assert route_back["affected_review_lanes"][0]["review_lane"] == "medical"

    forged_current = authority_records.paper_request(
        scope="publication_generation",
        stage_id="finalize_and_publication_handoff",
    )
    lane_state = next(
        item
        for item in forged_current["review_authority"]["currentness_receipt"][
            "lane_currentness"
        ]
        if item["review_lane"] == "medical"
    )
    lane_state["epistemic_currentness"] = authority_records.epistemic_currentness(
        forged_current["generation_manifest"],
        "medical",
        ignored_changes=[
            _epistemic_change(
                authority_records,
                node_ref="mas-member:analysis_output:primary",
                change_class="analysis_result",
                reason="outside_declared_evidence_graph",
            )
        ],
    )
    authority_records.reseal_review_currentness(forged_current)

    result = _evaluate(forged_current)

    route_back = _assert_finalize_route_back(
        result, "epistemic_review_scope_binding_required"
    )
    assert route_back["affected_review_lanes"][0]["review_lane"] == "medical"


def test_reviewer_revision_currentness_uses_existing_three_attempt_route_back_budget(
    authority_records: Any,
) -> None:
    def reviewer_revision_request(attempts_used: int) -> dict[str, Any]:
        request = authority_records.paper_request(
            scope="publication_generation",
            stage_id="finalize_and_publication_handoff",
        )
        authority_records.bind_revision_consumption(request)
        lane_state = next(
            item
            for item in request["review_authority"]["currentness_receipt"][
                "lane_currentness"
            ]
            if item["review_lane"] == "medical"
        )
        lane_state["epistemic_currentness"] = authority_records.epistemic_currentness(
            request["generation_manifest"],
            "medical",
            invalidating_changes=[
                _epistemic_change(
                    authority_records,
                    node_ref="mas-member:canonical_manuscript:primary",
                    change_class="claim",
                )
            ],
        )
        authority_records.reseal_review_currentness(request)
        request["repair_state"] = {
            "status": "pending" if attempts_used < 3 else "exhausted",
            "attempts_used": attempts_used,
            "max_attempts": 3,
            "repair_attempt_refs": [
                authority_records.typed_ref(
                    "opl_stage_attempt", f"reviewer-revision-{index}"
                )
                for index in range(attempts_used)
            ],
            "latest_repair_output_ref": (
                authority_records.typed_ref(
                    "opl_action_output", "reviewer-revision-latest"
                )
                if attempts_used
                else None
            ),
        }
        return request

    available = _evaluate(reviewer_revision_request(0))
    route_back = _assert_finalize_route_back(
        available, "independent_review_stale_after_epistemic_change"
    )
    assert route_back["remaining_repair_attempts"] == 3
    _output_validator().validate(available)

    exhausted = _evaluate(reviewer_revision_request(3))
    assert exhausted["status"] == "completed_with_quality_debt"
    assert exhausted["stage_outcome"]["stage_transition_allowed"] is True
    assert "review_scope_budget_exhausted" in exhausted["quality_debt"][
        "reason_codes"
    ]
    assert exhausted["route_back"]["remaining_repair_attempts"] == 0
    _output_validator().validate(exhausted)


def test_v2_fresh_review_without_snapshot_binding_is_invalid_host_input(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request(
        scope="manuscript_generation",
        stage_id="review_and_quality_gate",
        manifest_version=2,
    )
    wrapper = next(
        item
        for item in request["generation_manifest"]["independent_review_receipts"]
        if item["receipt"]["review_lane"] == "medical"
    )
    wrapper["receipt"].pop("review_input_snapshot_binding")
    authority_records.reseal_review_wrapper(wrapper)
    lane_state = next(
        item
        for item in request["review_authority"]["currentness_receipt"][
            "lane_currentness"
        ]
        if item["review_lane"] == "medical"
    )
    lane_state["current_review_receipt_ref"] = deepcopy(wrapper["receipt_ref"])
    authority_records.reseal_review_currentness(request)

    result = _evaluate(request)

    assert result["status"] == "invalid_host_input"
    assert "review_input_snapshot_binding" in result["error"]["detail"]


@pytest.mark.parametrize(
    "field",
    [
        "snapshot_manifest_ref",
        "owner_authority_ref",
        "producer_attempt_ref",
        "execution_content_binding_sha256",
    ],
)
def test_v2_present_snapshot_binding_requires_complete_generic_identity(
    authority_records: Any,
    field: str,
) -> None:
    request = authority_records.paper_request()
    wrapper = request["generation_manifest"]["independent_review_receipts"][0]
    wrapper["receipt"]["review_input_snapshot_binding"].pop(field)
    authority_records.reseal_review_wrapper(wrapper)

    result = _evaluate(request)

    assert result["status"] == "invalid_host_input"
    assert "review_input_snapshot_binding" in result["error"]["detail"]


def test_v2_snapshot_binding_rejects_forged_owner_authority_ref(
    authority_records: Any,
) -> None:
    request = authority_records.paper_request()
    wrapper = request["generation_manifest"]["independent_review_receipts"][0]
    binding = wrapper["receipt"]["review_input_snapshot_binding"]
    binding["owner_authority_ref"]["ref"] = (
        "mas-review-input-snapshot-authority:" + "0" * 64
    )
    authority_records.reseal_review_wrapper(wrapper)

    result = _evaluate(request)

    assert result["status"] == "invalid_host_input"
    assert "must bind canonical MAS authority bytes" in result["error"]["detail"]


def test_v2_origin_receipt_without_snapshot_binding_is_invalid_host_input(
    authority_records: Any,
) -> None:
    origin = authority_records.paper_request(
        manifest_version=2,
        generation_id="legacy-origin-generation",
    )
    origin_wrapper = next(
        item
        for item in origin["generation_manifest"]["independent_review_receipts"]
        if item["receipt"]["review_lane"] == "medical"
    )
    origin_wrapper["receipt"].pop("review_input_snapshot_binding")
    authority_records.reseal_review_wrapper(origin_wrapper)
    current = authority_records.paper_request(
        manifest_version=2,
        generation_id="current-generation-after-snapshot-contract",
    )
    _authorize_reused_lane(current, origin, "medical", authority_records)

    result = _evaluate(current)

    assert result["status"] == "invalid_host_input"
    assert "review_input_snapshot_binding" in result["error"]["detail"]


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

    route_back = _assert_finalize_route_back(
        result, "independent_review_receipt_not_current"
    )
    assert route_back["reason_code"] == "independent_review_receipt_not_current"
    assert route_back["affected_review_lanes"] == [
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
    figure_change = _epistemic_change(
        authority_records,
        node_ref="mas-member:figure_file:primary",
        change_class="visual_content",
    )
    for lane in ("display", "publication"):
        _authorize_reused_lane(
            current,
            origin,
            lane,
            authority_records,
            invalidating_changes=[figure_change],
        )

    result = _evaluate(current)

    route_back = _assert_finalize_route_back(
        result, "independent_review_stale_after_epistemic_change"
    )
    assert route_back["reason_code"] == (
        "independent_review_stale_after_epistemic_change"
    )
    assert route_back["resume_condition"] == (
        "refresh all affected review lanes in one pass: display, publication"
    )
    assert [item["review_lane"] for item in route_back["affected_review_lanes"]] == [
        "display",
        "publication",
    ]
    assert {item["reason_code"] for item in route_back["affected_review_lanes"]} == {
        "independent_review_stale_after_epistemic_change"
    }
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

    route_back = _assert_progress_debt(result, "independent_review_receipt_not_current")
    assert route_back["reason_code"] == "independent_review_receipt_not_current"


def test_manifest_and_review_currentness_versions_cannot_be_mixed(
    authority_records: Any,
) -> None:
    v1 = authority_records.paper_request(manifest_version=1)
    v2 = authority_records.paper_request(manifest_version=2)
    assert _evaluate(v1)["status"] == "completed_with_quality_debt"
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
    route_back = _assert_progress_debt(result, "review_request_authority_stale")
    assert route_back["reason_code"] == "review_request_authority_stale"
