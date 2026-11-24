"""Evaluate exact MAS paper-mission records without transport or I/O."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._generation_manifest import (
    EPISTEMIC_AUTHORITY_BOUNDARY,
    FIRST_DRAFT_QUALITY_ROUTE_PRIORITY,
    PROFESSIONAL_MANUSCRIPT_SKILL_INPUT_ROLES,
    PROFESSIONAL_MANUSCRIPT_SKILL_ROLES,
    REVIEW_LANE_ORDER,
    REVIEW_LANES_BY_SCOPE,
    epistemic_review_dependency_refs,
    first_draft_applicable_ref_fields,
    normalize_generation_manifest,
    require_stage_scope,
    review_scope_member_projection,
    source_input_digest,
)
from .._record_validation import (
    RequestShapeError,
    canonical_json_bytes,
    dedupe,
    enum_text,
    exact_ref as _exact_ref,
    exact_ref_list as _exact_ref_list,
    exact_keys,
    fingerprint,
    integer,
    mapping,
    optional_sha256,
    optional_text,
    optional_typed_ref as _optional_typed_ref,
    sequence,
    sha256,
    text,
    text_list,
    typed_ref as _typed_ref,
    typed_ref_list as _typed_ref_list,
)
from ..candidate_admission import normalize_candidate_admission_receipt

from .constants import (
    _EPISTEMIC_CHANGE_CLASS_BY_NODE_ROLE,
)

def _validate_review_currentness_receipt_ref(request: Mapping[str, Any]) -> None:
    authority = request["review_authority"]
    receipt_ref = authority["currentness_receipt_ref"]
    receipt = authority["currentness_receipt"]
    if (
        receipt_ref["ref"] != receipt["receipt_id"]
        or receipt_ref["size_bytes"] != receipt["receipt_size_bytes"]
        or receipt_ref["sha256"] != receipt["receipt_fingerprint"]
    ):
        raise RequestShapeError(
            "review currentness receipt ref does not match canonical receipt bytes"
        )


def _validate_selected_build_currentness_authority(
    request: Mapping[str, Any],
) -> None:
    authority = request["selected_build_currentness_authority"]
    selected_build = request["generation_manifest"].get("selected_build_binding")
    if authority is None or selected_build is None:
        return
    record = authority["authority_record"]
    receipt = selected_build["dependency_currentness_receipt"]
    host_authority_ref = request["host_context"][
        "build_dependency_currentness_authority_ref"
    ]
    host_issuer_attempt_ref = request["host_context"][
        "build_dependency_currentness_authority_issuer_attempt_ref"
    ]
    if host_authority_ref is None or host_issuer_attempt_ref is None:
        raise RequestShapeError(
            "selected build currentness authority requires host-bound authority refs"
        )
    if authority["authority_ref"] != host_authority_ref:
        raise RequestShapeError(
            "selected build currentness authority does not match host-bound authority ref"
        )
    if record["issuer_attempt_ref"] != host_issuer_attempt_ref:
        raise RequestShapeError(
            "selected build currentness authority issuer attempt does not match "
            "host-bound authority attempt"
        )
    if receipt["authority_ref"] != authority["authority_ref"]:
        raise RequestShapeError(
            "selected build currentness receipt does not bind the current owner "
            "authority record"
        )
    current_authority_refs = request["review_authority"]["currentness_receipt"].get(
        "current_build_dependency_authority_refs", []
    )
    if current_authority_refs != [authority["authority_ref"]]:
        raise RequestShapeError(
            "selected build currentness authority is not current in the MAS "
            "authority record"
        )
    if selected_build["dependency_currentness"] != "current":
        raise RequestShapeError(
            "selected build dependencies must be current for paper mission authority"
        )
    if not selected_build["root_matches_selected_bytes"]:
        raise RequestShapeError(
            "selected build root reader output must match selected build bytes"
        )
    if record["dependency_manifest_ref"] != selected_build["dependency_manifest_ref"]:
        raise RequestShapeError(
            "selected build currentness authority dependency manifest is not current"
        )
    if record["dependency_currentness"] != selected_build["dependency_currentness"]:
        raise RequestShapeError(
            "selected build currentness authority status does not match generation"
        )
    response_sync = request["generation_manifest"].get("reviewer_response_sync")
    if response_sync is None:
        raise RequestShapeError(
            "selected build currentness authority requires reviewer response currentness"
        )
    response_currentness = record["reviewer_response_currentness"]
    expected_response_currentness = {
        "generation_id": request["generation_manifest"]["generation_id"],
        "candidate_state": response_sync["candidate_state"],
        "response_ref": response_sync["response_ref"],
        "post_freeze_disposition": response_sync["post_freeze_disposition"],
        "external_synthesis_ref": response_sync["external_synthesis_ref"],
        "new_revision_ref": response_sync["new_revision_ref"],
    }
    if any(
        response_currentness[field] != expected
        for field, expected in expected_response_currentness.items()
    ):
        raise RequestShapeError(
            "selected build currentness authority does not bind current reviewer "
            "response generation and exact bytes"
        )
    if (
        response_sync["candidate_state"] == "frozen"
        and response_currentness["new_revision_ref"] is None
        and response_currentness["response_ref"]
        != response_currentness["prior_frozen_response_ref"]
    ):
        raise RequestShapeError(
            "same frozen generation cannot replace reviewer response exact bytes"
        )
    review_epoch = request["review_authority"]["currentness_receipt"][
        "authority_epoch"
    ]
    if record["authority_epoch"] != review_epoch:
        raise RequestShapeError(
            "selected build currentness authority epoch is not current"
        )
    issuer_attempt = record["issuer_attempt_ref"]
    producer_attempt = request["host_context"]["producer_attempt_ref"]
    if (
        issuer_attempt["ref"] == producer_attempt["ref"]
        or issuer_attempt["sha256"] == producer_attempt["sha256"]
    ):
        raise RequestShapeError(
            "selected build currentness authority issuer attempt must differ from "
            "generation producer attempt"
        )


def _validate_cross_record_lineage(request: Mapping[str, Any]) -> None:
    producer_attempt = request["host_context"]["producer_attempt_ref"]
    output_ref = request["host_context"]["output_ref"]
    currentness = request["review_authority"]["currentness_receipt"]
    lane_currentness = {
        item["review_lane"]: item for item in currentness.get("lane_currentness", [])
    }
    reviewer_attempts: list[tuple[str, str]] = []
    for wrapper in request["generation_manifest"]["independent_review_receipts"]:
        receipt = wrapper["receipt"]
        reviewer_attempt = receipt["reviewer_attempt_ref"]
        if (
            reviewer_attempt["ref"] == producer_attempt["ref"]
            or reviewer_attempt["sha256"] == producer_attempt["sha256"]
        ):
            raise RequestShapeError(
                "reviewer attempt must differ from producer attempt"
            )
        lane_status = lane_currentness.get(receipt["review_lane"], {}).get(
            "currentness_status", "fresh"
        )
        if lane_status == "fresh" and receipt["producer_output_ref"] != output_ref:
            raise RequestShapeError(
                "review receipt is not bound to the exact hosted output record"
            )
        reviewer_attempts.append((reviewer_attempt["ref"], reviewer_attempt["sha256"]))
    if len(reviewer_attempts) != len(set(reviewer_attempts)):
        raise RequestShapeError("review lanes require separate reviewer attempts")
    revision_binding = request["revision_consumption"]
    if revision_binding["binding_status"] == "bound":
        revision_receipt = revision_binding["consumption_receipt"]
        mission = request["mission"]
        if any(
            revision_receipt["mission_identity"][name] != mission[name]
            for name in ("program_id", "study_id", "mission_id")
        ):
            raise RequestShapeError(
                "revision consumption receipt mission_identity does not match the request"
            )
        if (
            revision_receipt["generation_id"]
            != request["generation_manifest"]["generation_id"]
        ):
            raise RequestShapeError(
                "revision consumption receipt generation_id does not match the manifest"
            )
        if revision_receipt["producer_attempt_ref"] != producer_attempt:
            raise RequestShapeError(
                "revision consumption receipt producer_attempt_ref does not match the host"
            )
        if revision_receipt["producer_output_ref"] != output_ref:
            raise RequestShapeError(
                "revision consumption receipt producer_output_ref does not match the host"
            )


def _candidate_admission_issue(
    request: Mapping[str, Any],
) -> tuple[str, str] | None:
    evidence_candidates = {
        (item["ref"], item["sha256"])
        for item in request["medical_evidence"]["candidate_artifact_refs"]
    }
    admissions = request["candidate_admissions"]
    admitted_candidates = {
        (
            item["receipt"]["candidate_ref"]["ref"],
            item["receipt"]["candidate_ref"]["sha256"],
        )
        for item in admissions
        if item["receipt"]["disposition"] == "accepted"
        and item["receipt"]["authorizes_manuscript_consumption"] is True
    }
    if evidence_candidates != admitted_candidates:
        return (
            "candidate_admission_receipt_required",
            "provide one exact current MAS acceptance receipt for every candidate",
        )

    manifest = request["generation_manifest"]
    source = source_input_digest(manifest)
    artifact_inventory = {
        (item["role"], item["ref"], item["size_bytes"], item["sha256"])
        for item in manifest["artifacts"]
    }
    mission = request["mission"]
    currentness = request["review_authority"]["currentness_receipt"]
    authority_epoch = currentness["authority_epoch"]
    supplied_receipts = {
        (
            item["receipt_ref"]["ref"],
            item["receipt_ref"]["size_bytes"],
            item["receipt_ref"]["sha256"],
        )
        for item in admissions
    }
    manifest_receipts = {
        (item["ref"], item["size_bytes"], item["sha256"])
        for item in manifest["artifacts"]
        if item["role"] == "candidate_admission_receipt"
    }
    if supplied_receipts != manifest_receipts:
        return (
            "candidate_admission_receipt_required",
            "embed every exact candidate admission receipt listed by the manifest",
        )
    for wrapper in admissions:
        receipt_ref = wrapper["receipt_ref"]
        receipt = wrapper["receipt"]
        if (
            receipt["disposition"] != "accepted"
            or receipt["authorizes_manuscript_consumption"] is not True
        ):
            return (
                "candidate_admission_receipt_required",
                "replace rejected or non-authorizing candidate receipts",
            )
        receipt_mission = receipt["mission_identity"]
        if any(
            receipt_mission[name] != mission[name]
            for name in ("program_id", "study_id", "mission_id")
        ):
            return (
                "candidate_admission_stale_after_generation_change",
                "re-adjudicate the candidate for the current mission",
            )
        candidate = receipt["candidate_ref"]
        evidence = receipt["evidence_refs"]
        source_receipt = receipt["source_input_digest"]
        stale = any(
            (
                currentness["schema_version"] == 1
                and receipt["authority_epoch"] != authority_epoch,
                receipt["generation_id"] != manifest["generation_id"],
                (
                    "source_input_digest",
                    source_receipt["ref"],
                    source_receipt["size_bytes"],
                    source_receipt["sha256"],
                )
                not in artifact_inventory,
                source_receipt["ref"] != source["ref"],
                source_receipt["size_bytes"] != source["size_bytes"],
                source_receipt["sha256"] != source["sha256"],
                (
                    "candidate_artifact",
                    candidate["ref"],
                    candidate["size_bytes"],
                    candidate["sha256"],
                )
                not in artifact_inventory,
                (
                    "candidate_admission_receipt",
                    receipt_ref["ref"],
                    receipt_ref["size_bytes"],
                    receipt_ref["sha256"],
                )
                not in artifact_inventory,
                any(
                    (
                        "evidence_record",
                        item["ref"],
                        item["size_bytes"],
                        item["sha256"],
                    )
                    not in artifact_inventory
                    for item in evidence
                ),
            )
        )
        if stale:
            return (
                "candidate_admission_stale_after_generation_change",
                "re-adjudicate exact candidate and evidence members for this generation",
            )
    return None


def _review_currentness_issue(
    request: Mapping[str, Any],
) -> tuple[str, str, list[dict[str, str]] | None] | None:
    currentness = request["review_authority"]["currentness_receipt"]
    if currentness["schema_version"] == 2:
        return _review_currentness_issue_v2(request)

    manifest = request["generation_manifest"]
    manifest_ref = request["generation_manifest_ref"]
    authority = request["review_authority"]
    currentness = authority["currentness_receipt"]
    review_request = authority["review_request_ref"]
    supplied_admissions = {
        (
            item["receipt_ref"]["ref"],
            item["receipt_ref"]["size_bytes"],
            item["receipt_ref"]["sha256"],
        )
        for item in request["candidate_admissions"]
    }
    current_admissions = {
        (item["ref"], item["size_bytes"], item["sha256"])
        for item in currentness["current_candidate_admission_receipt_refs"]
    }
    supplied_reviews = {
        (
            item["receipt_ref"]["ref"],
            item["receipt_ref"]["size_bytes"],
            item["receipt_ref"]["sha256"],
        )
        for item in manifest["independent_review_receipts"]
    }
    current_reviews = {
        (item["ref"], item["size_bytes"], item["sha256"])
        for item in currentness["current_review_receipt_refs"]
    }
    review_identity = (
        review_request["ref"],
        review_request["size_bytes"],
        review_request["sha256"],
    )
    superseded_reviews = {
        (item["ref"], item["size_bytes"], item["sha256"])
        for item in currentness["superseded_review_request_refs"]
    }
    if any(
        (
            currentness["current_generation_id"] != manifest["generation_id"],
            currentness["current_generation_manifest_ref"] != manifest_ref,
            currentness["current_review_request_ref"] != review_request,
            supplied_admissions != current_admissions,
            manifest["generation_id"] in currentness["superseded_generation_ids"],
            review_identity in superseded_reviews,
        )
    ):
        return (
            "review_request_authority_stale",
            "supply the current review request, generation, and candidate receipts",
            None,
        )
    reviews = manifest["independent_review_receipts"]
    required_lanes = REVIEW_LANES_BY_SCOPE[manifest["manifest_scope"]]
    review_lanes = {item["receipt"]["review_lane"] for item in reviews}
    if not required_lanes <= review_lanes:
        return (
            "independent_reviewer_record_required",
            "provide one exact current receipt for every required review lane",
            None,
        )
    if supplied_reviews != current_reviews:
        return (
            "independent_review_receipt_not_current",
            "supply the exact review receipt inventory authorized by MAS currentness",
            None,
        )
    if any(
        item["receipt"]["authority_epoch"] != currentness["authority_epoch"]
        or item["receipt"]["review_request_ref"] != review_request
        for item in reviews
    ):
        return (
            "independent_review_stale_after_canonical_change",
            "replace receipts issued for an older authority epoch or review request",
            None,
        )
    affected = [
        {
            "review_lane": lane,
            "reason_code": "review_input_snapshot_binding_required",
            "resume_condition": (
                f"obtain a fresh {lane} review over the immutable input snapshot"
            ),
        }
        for lane in REVIEW_LANE_ORDER
        if lane in required_lanes
    ]
    return (
        "review_input_snapshot_binding_required",
        "replace legacy review receipts with immutable snapshot-bound receipts",
        affected,
    )


def _review_currentness_issue_v2(
    request: Mapping[str, Any],
) -> tuple[str, str, list[dict[str, str]] | None] | None:
    manifest = request["generation_manifest"]
    manifest_ref = request["generation_manifest_ref"]
    authority = request["review_authority"]
    currentness = authority["currentness_receipt"]
    review_request = authority["review_request_ref"]
    supplied_admissions = {
        _exact_ref_identity(item["receipt_ref"])
        for item in request["candidate_admissions"]
    }
    current_admissions = {
        _exact_ref_identity(item)
        for item in currentness["current_candidate_admission_receipt_refs"]
    }
    if any(
        (
            manifest["schema_version"] != 2,
            currentness["current_generation_id"] != manifest["generation_id"],
            currentness["current_generation_manifest_ref"] != manifest_ref,
            currentness["current_review_request_ref"] != review_request,
            supplied_admissions != current_admissions,
        )
    ):
        return (
            "review_request_authority_stale",
            "supply the current generation, review request, and candidate receipts",
            None,
        )

    required_lanes = REVIEW_LANES_BY_SCOPE[manifest["manifest_scope"]]
    reviews = {
        item["receipt"]["review_lane"]: item
        for item in manifest["independent_review_receipts"]
    }
    lane_currentness = {
        item["review_lane"]: item for item in currentness["lane_currentness"]
    }
    scopes = {item["review_lane"]: item for item in manifest["review_scopes"]}
    if not required_lanes <= set(reviews):
        return (
            "independent_reviewer_record_required",
            "provide one exact current receipt for every required review lane",
            None,
        )
    if set(lane_currentness) != required_lanes:
        return (
            "independent_review_receipt_not_current",
            "supply one lane currentness record for every required review lane",
            None,
        )

    affected_review_lanes: list[dict[str, str]] = []
    for lane in REVIEW_LANE_ORDER:
        if lane not in required_lanes:
            continue
        wrapper = reviews[lane]
        receipt = wrapper["receipt"]
        lane_state = lane_currentness[lane]
        scope = scopes[lane]
        epistemic_scope = scope["epistemic_scope"]
        epistemic_currentness = lane_state["epistemic_currentness"]
        lane_issue: tuple[str, str] | None = None
        if any(
            (
                lane_state["current_rubric_ref"] != receipt["rubric_ref"],
                receipt["review_scope_sha256"] != lane_state["review_scope_sha256"],
                lane_state["current_review_receipt_ref"] != wrapper["receipt_ref"],
                lane_state["current_review_request_ref"]
                != receipt["review_request_ref"],
                lane_state["review_authority_epoch"] != receipt["authority_epoch"],
                lane_state["review_receipt_issued_generation_id"]
                != receipt["issued_generation_id"],
                lane_state["review_receipt_issued_generation_manifest_sha256"]
                != receipt["issued_generation_manifest_sha256"],
                _exact_ref_identity(lane_state["current_review_request_ref"])
                in {
                    _exact_ref_identity(item)
                    for item in lane_state["superseded_review_request_refs"]
                },
            )
        ):
            lane_issue = (
                "independent_review_receipt_not_current",
                f"replace stale {lane} lane currentness and receipt bindings",
            )
        elif any(
            (
                lane_state["review_scope_sha256"] != scope["review_scope_sha256"],
                epistemic_currentness["scope_id"] != epistemic_scope["scope_id"],
                epistemic_currentness["scope_kind"]
                != epistemic_scope["scope_kind"],
                epistemic_currentness["reviewed_dependency_refs"]
                != epistemic_review_dependency_refs(epistemic_scope),
                not _epistemic_evaluation_matches_scope(
                    epistemic_currentness,
                    epistemic_scope,
                ),
            )
        ):
            lane_issue = (
                "epistemic_review_scope_binding_required",
                f"bind {lane} currentness to the current MAS dependency scope",
            )
        elif epistemic_currentness["status"] == "stale":
            lane_issue = (
                "independent_review_stale_after_epistemic_change",
                f"obtain a fresh {lane} review for its changed semantic dependencies",
            )
        else:
            receipt_admissions = {
                _exact_ref_identity(item)
                for item in receipt["accepted_candidate_receipt_refs"]
            }
            reuse_provenance = lane_state["reuse_provenance"]
            if lane_issue is not None:
                affected_review_lanes.append(
                    {
                        "review_lane": lane,
                        "reason_code": lane_issue[0],
                        "resume_condition": lane_issue[1],
                    }
                )
                continue
            if lane_state["currentness_status"] == "fresh":
                if any(
                    (
                        receipt["issued_generation_id"] != manifest["generation_id"],
                        receipt["issued_generation_manifest_sha256"]
                        != manifest["generation_manifest_sha256"],
                        receipt_admissions != current_admissions,
                        review_scope_member_projection(receipt["reviewed_members"])
                        != review_scope_member_projection(scope["reviewed_members"]),
                    )
                ):
                    lane_issue = (
                        "independent_review_stale_after_canonical_change",
                        f"refresh {lane} review against current candidate admissions",
                    )
            else:
                provenance = reuse_provenance
                if provenance is None or any(
                    (
                        provenance["origin_generation_id"] == manifest["generation_id"],
                        provenance["origin_generation_manifest_ref"] == manifest_ref,
                        provenance["origin_generation_id"]
                        != receipt["issued_generation_id"],
                        provenance["origin_generation_manifest_ref"]["sha256"]
                        != receipt["issued_generation_manifest_sha256"],
                        provenance["origin_review_request_ref"]
                        != receipt["review_request_ref"],
                        provenance["origin_review_receipt_ref"]
                        != wrapper["receipt_ref"],
                        provenance["origin_review_scope_sha256"]
                        != receipt["review_scope_sha256"],
                        _review_member_semantic_identities(receipt["reviewed_members"])
                        != _review_member_semantic_identities(scope["reviewed_members"]),
                        receipt_admissions
                        != {
                            _exact_ref_identity(item)
                            for item in provenance[
                                "origin_candidate_admission_receipt_refs"
                            ]
                        },
                    )
                ):
                    lane_issue = (
                        "independent_review_stale_after_scope_change",
                        f"obtain a fresh {lane} review because exact scope reuse is unproven",
                    )
        if lane_issue is not None:
            affected_review_lanes.append(
                {
                    "review_lane": lane,
                    "reason_code": lane_issue[0],
                    "resume_condition": lane_issue[1],
                }
            )
    if affected_review_lanes:
        reason_codes = {item["reason_code"] for item in affected_review_lanes}
        reason_code = (
            affected_review_lanes[0]["reason_code"]
            if len(reason_codes) == 1
            else "independent_review_receipt_not_current"
        )
        resume_condition = (
            affected_review_lanes[0]["resume_condition"]
            if len(affected_review_lanes) == 1
            else "refresh all affected review lanes in one pass: "
            + ", ".join(item["review_lane"] for item in affected_review_lanes)
        )
        return reason_code, resume_condition, affected_review_lanes
    return None


def _epistemic_evaluation_matches_scope(
    evaluation: Mapping[str, Any],
    scope: Mapping[str, Any],
) -> bool:
    """Verify that a consumed Framework evaluation binds the declared MAS graph."""

    dependency_refs = set(epistemic_review_dependency_refs(scope))
    nodes_by_ref = {item["node_ref"]: item for item in scope["nodes"]}
    for change in [
        *evaluation["invalidating_changes"],
        *evaluation["ignored_changes"],
    ]:
        node = nodes_by_ref.get(change["node_ref"])
        if node is not None and change["change_class"] != "locator_only":
            if (
                _EPISTEMIC_CHANGE_CLASS_BY_NODE_ROLE.get(node["role"])
                != change["change_class"]
            ):
                return False
    if any(
        change["node_ref"] not in dependency_refs
        for change in evaluation["invalidating_changes"]
    ):
        return False
    for change in evaluation["ignored_changes"]:
        node = nodes_by_ref.get(change["node_ref"])
        reason = change["reason"]
        if reason == "outside_declared_evidence_graph" and node is not None:
            return False
        if reason == "outside_reviewed_dependency_closure" and (
            node is None or change["node_ref"] in dependency_refs
        ):
            return False
        if reason == "locator_or_non_semantic_change_only" and not (
            change["change_class"] == "locator_only"
            or change["semantic_changed"] is False
        ):
            return False
        if reason == "governance_or_review_metadata_is_not_content_evidence" and (
            node is None
            or node["role"] not in {"governance_metadata", "review_receipt"}
        ):
            return False
        if (
            change["node_ref"] in dependency_refs
            and change["semantic_changed"] is True
            and change["change_class"] != "locator_only"
        ):
            return False
    return True


def _review_member_semantic_identities(
    members: list[dict[str, Any]],
) -> list[tuple[str, str]]:
    return sorted((item["member_id"], item["role"]) for item in members)


def _revision_consumption_issue(
    request: Mapping[str, Any],
) -> tuple[str, str] | None:
    binding = request["revision_consumption"]
    if binding["binding_status"] != "bound":
        return (
            "revision_consumption_binding_required",
            "bind this generation to an explicit no-revision or consumed-revision receipt",
        )
    current_revision_refs = binding[
        "current_accepted_or_active_revision_intake_refs"
    ]
    if current_revision_refs is None:
        return (
            "revision_currentness_inventory_required",
            "bind the current accepted or active workspace revision-intake refs before "
            "claiming revision currentness",
        )
    receipt = binding["consumption_receipt"]
    current_revision_identities = {
        _exact_ref_identity(item) for item in current_revision_refs
    }
    consumed_revision_identities = {
        _exact_ref_identity(item)
        for item in receipt["consumed_revision_refs"]
        if item["kind"] == "opl_revision_intake"
    }
    if not current_revision_identities.issubset(consumed_revision_identities):
        return (
            "latest_accepted_or_active_revision_not_consumed",
            "consume every current accepted or active workspace revision intake in this "
            "generation before finalize or publication handoff",
        )
    if receipt["applicability"] == "revision_consumed" and any(
        item["status"] != "closed" for item in receipt["finding_closures"]
    ):
        return (
            "revision_finding_closure_incomplete",
            "close or explicitly carry forward every consumed OPL finding before "
            "quality acceptance",
        )
    return None


def _exact_ref_identity(value: Mapping[str, Any]) -> tuple[str, int, str]:
    return (value["ref"], value["size_bytes"], value["sha256"])
