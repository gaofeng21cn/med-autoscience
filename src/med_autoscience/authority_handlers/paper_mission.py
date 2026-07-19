"""Evaluate exact MAS paper-mission records without transport or I/O."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._generation_manifest import (
    EPISTEMIC_AUTHORITY_BOUNDARY,
    PROFESSIONAL_MANUSCRIPT_SKILL_ROLES,
    REVIEW_LANE_ORDER,
    REVIEW_LANES_BY_SCOPE,
    epistemic_review_dependency_refs,
    normalize_generation_manifest,
    require_stage_scope,
    review_scope_member_projection,
    source_input_digest,
)
from ._record_validation import (
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
from .candidate_admission import normalize_candidate_admission_receipt


REQUEST_KIND = "mas_paper_mission_authority_request"
RESULT_KIND = "mas_paper_mission_authority_result"
SCHEMA_VERSION = 2

_HARD_GATE_KINDS = frozenset(
    {
        "medical_safety",
        "source_identity",
        "source_currentness",
        "domain_authority",
        "credential",
        "irreversible_action",
    }
)
_AUTHORITY_BOUNDARY = {
    "owner": "MedAutoScience",
    "handler_role": "validate_exact_candidate_and_review_receipts_and_return_owner_result",
    "opl_role": "verify_exact_ref_bytes_inject_typed_records_and_persist_exact_result_bytes",
    "program_originates_medical_quality_verdict": False,
    "host_completion_counts_as_domain_completion": False,
    "selects_next_stage": False,
    "owns_profile_or_path_discovery": False,
    "owns_workspace_or_source_discovery": False,
    "owns_queue_session_dag_or_attempt_lifecycle": False,
    "owns_runtime_ledger": False,
    "performs_filesystem_io": False,
    "performs_network_io": False,
    "spawns_process_or_executor": False,
    "invokes_opl_or_codex": False,
    "authorizes_publication_or_submission": False,
}
_SNAPSHOT_AUTHORITY_BOUNDARY = {
    "storage_role": "immutable_reviewer_input_transport",
    "mas_selects_review_lane_scope_and_members": True,
    "framework_can_select_or_narrow_members": False,
    "framework_can_interpret_member_roles": False,
    "framework_can_write_domain_truth": False,
    "framework_can_sign_reviewer_receipt": False,
    "framework_can_sign_owner_receipt": False,
    "framework_can_create_typed_blocker": False,
    "framework_can_claim_quality_readiness": False,
    "framework_can_claim_publication_readiness": False,
    "framework_can_claim_artifact_authority": False,
}
_REVISION_CONSUMPTION_AUTHORITY_BOUNDARY = {
    "receipt_can_authorize_review_verdict": False,
    "receipt_can_authorize_owner_receipt": False,
    "receipt_can_authorize_publication": False,
    "receipt_can_authorize_submission": False,
    "receipt_can_create_typed_blocker": False,
}
_EPISTEMIC_CHANGE_CLASSES = {
    "data",
    "context",
    "analysis_code",
    "analysis_parameters",
    "analysis_result",
    "claim",
    "reference_source",
    "citation_linkage",
    "limitation",
    "visual_content",
    "layout",
    "render_template",
    "package_composition",
    "package_wrapper",
    "governance_metadata",
    "review_receipt",
    "locator_only",
}
_EPISTEMIC_IGNORED_REASONS = {
    "outside_declared_evidence_graph",
    "locator_or_non_semantic_change_only",
    "governance_or_review_metadata_is_not_content_evidence",
    "outside_reviewed_dependency_closure",
}
_EPISTEMIC_CHANGE_CLASS_BY_NODE_ROLE = {
    "source_data": "data",
    "context": "context",
    "analysis_code": "analysis_code",
    "analysis_parameters": "analysis_parameters",
    "analysis_result": "analysis_result",
    "claim": "claim",
    "reference_source": "reference_source",
    "citation_linkage": "citation_linkage",
    "limitation": "limitation",
    "reproduction_instruction": None,
    "visual_content": "visual_content",
    "layout": "layout",
    "render_template": "render_template",
    "package_content": "package_composition",
    "package_wrapper": "package_wrapper",
    "governance_metadata": "governance_metadata",
    "review_receipt": "review_receipt",
}


def evaluate_paper_mission_authority(request: Mapping[str, Any]) -> dict[str, Any]:
    """Return a deterministic owner result over host-injected exact records."""

    try:
        normalized = _normalize_request(request)
        _validate_cross_record_lineage(normalized)
    except RequestShapeError as error:
        return _invalid_host_input(str(error))

    hard_gate = normalized["hard_gate"]
    if hard_gate["kind"] == "human_decision":
        return _finalize(
            normalized,
            status="human_gate",
            stage_outcome=_stage_outcome("human_gate", transition_allowed=False),
            human_gate=_human_gate(normalized),
        )
    if hard_gate["kind"] in _HARD_GATE_KINDS:
        return _finalize(
            normalized,
            status="typed_blocker",
            stage_outcome=_stage_outcome("typed_blocker", transition_allowed=False),
            typed_blocker=_typed_blocker(normalized),
        )

    evidence = normalized["medical_evidence"]
    if evidence["source_readiness_status"] != "ready":
        return _route_result(
            normalized,
            reason_code="source_readiness_record_required",
            next_owner="mas_source_readiness_owner",
            resume_condition="provide a current MAS source-readiness receipt",
        )
    if evidence["claim_evidence_status"] != "aligned":
        return _route_result(
            normalized,
            reason_code="claim_evidence_alignment_required",
            next_owner="mission_executor",
            resume_condition="repair claim boundaries against accepted evidence",
        )
    if not evidence["evidence_refs"] and not evidence["negative_result_refs"]:
        return _route_result(
            normalized,
            reason_code="medical_evidence_record_required",
            next_owner="mission_executor",
            resume_condition="provide accepted evidence or a negative-result record",
        )

    # Admission is a pre-authoring gate and is evaluated before hosted output state.
    candidate_issue = _candidate_admission_issue(normalized)
    if candidate_issue is not None:
        return _route_result(
            normalized,
            reason_code=candidate_issue[0],
            next_owner="mas_candidate_admission_owner",
            resume_condition=candidate_issue[1],
        )

    host = normalized["host_context"]
    if host["output_state"] != "consumable" or not evidence["candidate_artifact_refs"]:
        if normalized["mission"]["stage_id"] == "finalize_and_publication_handoff":
            return _route_result(
                normalized,
                reason_code="consumable_output_missing",
                next_owner="mission_executor",
                resume_condition="produce the complete publication-generation output",
            )
        route_back = _route_back(
            normalized,
            reason_code="consumable_output_missing",
            next_owner="mission_executor",
            resume_condition="produce a readable candidate output bound to the hosted attempt",
        )
        return _finalize(
            normalized,
            status="completed_with_quality_debt",
            stage_outcome=_stage_outcome(
                "completed_with_quality_debt", transition_allowed=True
            ),
            route_back=route_back,
            quality_debt=_quality_debt(
                normalized, reason_codes=["consumable_output_missing"]
            ),
        )

    professional_debt = _professional_manuscript_skill_quality_debt(normalized)
    if professional_debt:
        return _professional_skill_debt_result(
            normalized,
            reason_codes=professional_debt,
            resume_condition=(
                "consume every required manuscript, statistical, table, and submission "
                "Skill and bind its receipt to the exact generation artifacts"
            ),
        )
    professional_figure_debt = _professional_figure_skill_quality_debt(normalized)
    if professional_figure_debt:
        return _professional_skill_debt_result(
            normalized,
            reason_codes=professional_figure_debt,
            resume_condition=(
                "consume the required professional Figure Skills and bind their "
                "receipts to the exact final figure bytes"
            ),
        )

    review_issue = _review_currentness_issue(normalized)
    if review_issue is not None:
        affected_lanes = review_issue[2]
        reason_codes = (
            dedupe([item["reason_code"] for item in affected_lanes])
            if affected_lanes
            else [review_issue[0]]
        )
        if normalized["generation_manifest"]["manifest_scope"] == (
            "manuscript_generation"
        ):
            reason_codes = dedupe(
                ["first_draft_cross_domain_pre_review_missing_or_stale", *reason_codes]
            )
        if _is_reviewer_revision(normalized):
            route_back = _route_back(
                normalized,
                reason_code=review_issue[0],
                next_owner="independent_reviewer",
                resume_condition=review_issue[1],
                affected_review_lanes=affected_lanes,
            )
            repair = normalized["repair_state"]
            if repair["attempts_used"] < repair["max_attempts"]:
                return _finalize(
                    normalized,
                    status="route_back",
                    stage_outcome=_stage_outcome(
                        "route_back", transition_allowed=False
                    ),
                    route_back=route_back,
                )
            return _finalize(
                normalized,
                status="completed_with_quality_debt",
                stage_outcome=_stage_outcome(
                    "completed_with_quality_debt", transition_allowed=True
                ),
                route_back=route_back,
                quality_debt=_quality_debt(
                    normalized,
                    reason_codes=dedupe(
                        [*reason_codes, "review_scope_budget_exhausted"]
                    ),
                ),
            )
        if normalized["mission"]["stage_id"] == "finalize_and_publication_handoff":
            return _route_result(
                normalized,
                reason_code=review_issue[0],
                next_owner="independent_reviewer",
                resume_condition=review_issue[1],
                affected_review_lanes=affected_lanes,
            )
        route_back = _route_back(
            normalized,
            reason_code=review_issue[0],
            next_owner="independent_reviewer",
            resume_condition=review_issue[1],
            affected_review_lanes=affected_lanes,
        )
        return _finalize(
            normalized,
            status="completed_with_quality_debt",
            stage_outcome=_stage_outcome(
                "completed_with_quality_debt", transition_allowed=True
            ),
            route_back=route_back,
            quality_debt=_quality_debt(
                normalized,
                reason_codes=reason_codes,
            ),
        )

    revision_issue = _revision_consumption_issue(normalized)
    if revision_issue is not None:
        route_back = _route_back(
            normalized,
            reason_code=revision_issue[0],
            next_owner="mas_revision_consumption_owner",
            resume_condition=revision_issue[1],
        )
        return _finalize(
            normalized,
            status="completed_with_quality_debt",
            stage_outcome=_stage_outcome(
                "completed_with_quality_debt", transition_allowed=True
            ),
            route_back=route_back,
            quality_debt=_quality_debt(
                normalized,
                reason_codes=[revision_issue[0]],
            ),
        )

    review_status = _aggregate_review_status(normalized)
    repair = normalized["repair_state"]
    if review_status in {"revision_required", "rejected"}:
        reason_code = (
            "independent_review_rejected_output"
            if review_status == "rejected"
            else "independent_review_requires_repair"
        )
        route_back = _route_back(
            normalized,
            reason_code=reason_code,
            next_owner="mission_repairer",
            resume_condition="repair the exact manifest and obtain fresh review receipts",
        )
        if (
            repair["attempts_used"] < repair["max_attempts"]
            or normalized["mission"]["stage_id"] == "finalize_and_publication_handoff"
        ):
            return _finalize(
                normalized,
                status="route_back",
                stage_outcome=_stage_outcome("route_back", transition_allowed=False),
                route_back=route_back,
            )
        return _finalize(
            normalized,
            status="completed_with_quality_debt",
            stage_outcome=_stage_outcome(
                "completed_with_quality_debt", transition_allowed=True
            ),
            route_back=route_back,
            quality_debt=_quality_debt(
                normalized,
                reason_codes=[reason_code, "repair_budget_exhausted"],
            ),
        )

    debt_codes, defect_refs = _review_quality_debt(normalized)
    if debt_codes or defect_refs:
        if normalized["mission"]["stage_id"] == "finalize_and_publication_handoff":
            return _route_result(
                normalized,
                reason_code="independent_review_quality_debt_open",
                next_owner="mission_repairer",
                resume_condition="close every review defect and obtain fresh passed receipts",
            )
        reason_codes = [*debt_codes]
        if defect_refs:
            reason_codes.append("independent_review_open_defects")
        return _finalize(
            normalized,
            status="completed_with_quality_debt",
            stage_outcome=_stage_outcome(
                "completed_with_quality_debt", transition_allowed=True
            ),
            quality_debt=_quality_debt(normalized, reason_codes=dedupe(reason_codes)),
        )

    return _finalize(
        normalized,
        status="owner_receipt",
        stage_outcome=_stage_outcome("completed", transition_allowed=True),
        owner_receipt=_owner_receipt(normalized),
    )


def _is_reviewer_revision(request: Mapping[str, Any]) -> bool:
    receipt = request["revision_consumption"]["consumption_receipt"]
    return receipt["applicability"] == "revision_consumed"


def _normalize_request(request: Mapping[str, Any]) -> dict[str, Any]:
    payload = mapping(request, "request")
    request_keys = {
        "surface_kind",
        "schema_version",
        "host_context",
        "mission",
        "medical_evidence",
        "generation_manifest",
        "generation_manifest_ref",
        "candidate_admissions",
        "review_authority",
        "repair_state",
        "hard_gate",
    }
    if "revision_consumption" in payload:
        request_keys.add("revision_consumption")
    exact_keys(
        payload,
        request_keys,
        "request",
    )
    if payload.get("surface_kind") != REQUEST_KIND:
        raise RequestShapeError(f"surface_kind must be {REQUEST_KIND}")
    if payload.get("schema_version") != SCHEMA_VERSION or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError("schema_version must be integer 2")

    mission = _normalize_mission(payload.get("mission"))
    manifest = normalize_generation_manifest(payload.get("generation_manifest"))
    require_stage_scope(mission["stage_id"], manifest["manifest_scope"])
    manifest_ref = _exact_ref(
        payload.get("generation_manifest_ref"),
        "generation_manifest_ref",
        "mas_generation_manifest",
    )
    if (
        manifest_ref["sha256"] != manifest["generation_manifest_sha256"]
        or manifest_ref["size_bytes"] != manifest["generation_manifest_size_bytes"]
    ):
        raise RequestShapeError(
            "generation_manifest_ref size/hash does not match canonical manifest"
        )
    if "revision_consumption" in payload and payload["revision_consumption"] is None:
        raise RequestShapeError("revision_consumption must be an object when supplied")
    normalized = {
        "surface_kind": REQUEST_KIND,
        "schema_version": SCHEMA_VERSION,
        "host_context": _normalize_host_context(payload.get("host_context")),
        "mission": mission,
        "medical_evidence": _normalize_medical_evidence(
            payload.get("medical_evidence")
        ),
        "generation_manifest": manifest,
        "generation_manifest_ref": manifest_ref,
        "candidate_admissions": _normalize_candidate_admissions(
            payload.get("candidate_admissions")
        ),
        "review_authority": _normalize_review_authority(
            payload.get("review_authority")
        ),
        "revision_consumption": _normalize_revision_consumption(
            payload.get("revision_consumption")
        ),
        "repair_state": _normalize_repair(payload.get("repair_state")),
        "hard_gate": _normalize_hard_gate(payload.get("hard_gate")),
    }
    currentness_version = normalized["review_authority"]["currentness_receipt"][
        "schema_version"
    ]
    if manifest["schema_version"] != currentness_version:
        raise RequestShapeError(
            "generation manifest and review currentness schema versions must match"
        )
    _validate_review_currentness_receipt_ref(normalized)
    return normalized


def _normalize_host_context(value: Any) -> dict[str, Any]:
    field = "host_context"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {"action_id", "run_ref", "producer_attempt_ref", "output_ref", "output_state"},
        field,
    )
    if payload.get("action_id") != "paper_mission":
        raise RequestShapeError("host_context.action_id must be paper_mission")
    return {
        "action_id": "paper_mission",
        "run_ref": _typed_ref(
            payload.get("run_ref"), f"{field}.run_ref", "opl_stage_run"
        ),
        "producer_attempt_ref": _typed_ref(
            payload.get("producer_attempt_ref"),
            f"{field}.producer_attempt_ref",
            "opl_stage_attempt",
        ),
        "output_ref": _exact_ref(
            payload.get("output_ref"),
            f"{field}.output_ref",
            "opl_action_output",
        ),
        "output_state": enum_text(
            payload.get("output_state"),
            f"{field}.output_state",
            {"consumable", "no_output", "damaged", "failed"},
        ),
    }


def _normalize_mission(value: Any) -> dict[str, Any]:
    field = "mission"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {"program_id", "study_id", "mission_id", "stage_id", "stage_goal_ref"},
        field,
    )
    return {
        "program_id": text(payload.get("program_id"), f"{field}.program_id"),
        "study_id": text(payload.get("study_id"), f"{field}.study_id"),
        "mission_id": text(payload.get("mission_id"), f"{field}.mission_id"),
        "stage_id": text(payload.get("stage_id"), f"{field}.stage_id"),
        "stage_goal_ref": _typed_ref(
            payload.get("stage_goal_ref"),
            f"{field}.stage_goal_ref",
            "mas_stage_goal",
        ),
    }


def _normalize_medical_evidence(value: Any) -> dict[str, Any]:
    field = "medical_evidence"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "source_readiness_status",
            "source_readiness_receipt_ref",
            "claim_evidence_status",
            "claim_boundary_ref",
            "candidate_artifact_refs",
            "evidence_refs",
            "negative_result_refs",
            "failed_path_refs",
            "artifact_lineage_refs",
            "reproducibility_refs",
        },
        field,
    )
    source_status = enum_text(
        payload.get("source_readiness_status"),
        f"{field}.source_readiness_status",
        {"ready", "not_ready", "unknown"},
    )
    source_ref = _optional_typed_ref(
        payload.get("source_readiness_receipt_ref"),
        f"{field}.source_readiness_receipt_ref",
        "mas_source_readiness_receipt",
    )
    if source_status == "ready" and source_ref is None:
        raise RequestShapeError(
            "ready source status requires source_readiness_receipt_ref"
        )
    return {
        "source_readiness_status": source_status,
        "source_readiness_receipt_ref": source_ref,
        "claim_evidence_status": enum_text(
            payload.get("claim_evidence_status"),
            f"{field}.claim_evidence_status",
            {"aligned", "revision_required", "unsafe", "unknown"},
        ),
        "claim_boundary_ref": _typed_ref(
            payload.get("claim_boundary_ref"),
            f"{field}.claim_boundary_ref",
            "mas_claim_boundary",
        ),
        "candidate_artifact_refs": _typed_ref_list(
            payload.get("candidate_artifact_refs"),
            f"{field}.candidate_artifact_refs",
            "mas_artifact",
        ),
        "evidence_refs": _typed_ref_list(
            payload.get("evidence_refs"), f"{field}.evidence_refs", "mas_evidence"
        ),
        "negative_result_refs": _typed_ref_list(
            payload.get("negative_result_refs"),
            f"{field}.negative_result_refs",
            "mas_negative_result",
        ),
        "failed_path_refs": _typed_ref_list(
            payload.get("failed_path_refs"),
            f"{field}.failed_path_refs",
            "mas_failed_path",
        ),
        "artifact_lineage_refs": _typed_ref_list(
            payload.get("artifact_lineage_refs"),
            f"{field}.artifact_lineage_refs",
            "mas_artifact_lineage",
        ),
        "reproducibility_refs": _typed_ref_list(
            payload.get("reproducibility_refs"),
            f"{field}.reproducibility_refs",
            "mas_reproducibility",
        ),
    }


def _normalize_candidate_admissions(value: Any) -> list[dict[str, Any]]:
    field = "candidate_admissions"
    admissions: list[dict[str, Any]] = []
    for index, item in enumerate(sequence(value, field)):
        item_field = f"{field}[{index}]"
        payload = mapping(item, item_field)
        exact_keys(payload, {"receipt_ref", "receipt"}, item_field)
        receipt_ref = _exact_ref(
            payload.get("receipt_ref"),
            f"{item_field}.receipt_ref",
            "mas_candidate_admission_receipt",
        )
        receipt = normalize_candidate_admission_receipt(
            payload.get("receipt"), f"{item_field}.receipt"
        )
        if (
            receipt_ref["ref"] != receipt["receipt_id"]
            or receipt_ref["size_bytes"] != receipt["receipt_size_bytes"]
            or receipt_ref["sha256"] != receipt["receipt_fingerprint"]
        ):
            raise RequestShapeError(
                f"{item_field}.receipt_ref does not match canonical receipt bytes"
            )
        admissions.append({"receipt_ref": receipt_ref, "receipt": receipt})
    identities = [
        (item["receipt_ref"]["ref"], item["receipt_ref"]["sha256"])
        for item in admissions
    ]
    candidates = [item["receipt"]["candidate_id"] for item in admissions]
    if len(identities) != len(set(identities)) or len(candidates) != len(
        set(candidates)
    ):
        raise RequestShapeError("candidate_admissions contains duplicate receipts")
    return admissions


def _normalize_revision_consumption(value: Any) -> dict[str, Any]:
    field = "revision_consumption"
    if value is None:
        return {
            "binding_status": "legacy_unbound",
            "consumption_receipt_ref": None,
            "consumption_receipt": None,
        }
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "surface_kind",
            "schema_version",
            "consumption_receipt_ref",
            "consumption_receipt",
        },
        field,
    )
    if payload.get("surface_kind") != "mas_revision_consumption_binding":
        raise RequestShapeError(
            f"{field}.surface_kind must be mas_revision_consumption_binding"
        )
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 1")
    receipt_ref = _exact_ref(
        payload.get("consumption_receipt_ref"),
        f"{field}.consumption_receipt_ref",
        "mas_revision_consumption_receipt",
    )
    receipt = _normalize_revision_consumption_receipt(
        payload.get("consumption_receipt"),
        f"{field}.consumption_receipt",
    )
    if (
        receipt_ref["ref"] != receipt["receipt_id"]
        or receipt_ref["size_bytes"] != receipt["receipt_size_bytes"]
        or receipt_ref["sha256"] != receipt["receipt_fingerprint"]
    ):
        raise RequestShapeError(
            f"{field}.consumption_receipt_ref does not match canonical receipt bytes"
        )
    return {
        "binding_status": "bound",
        "surface_kind": "mas_revision_consumption_binding",
        "schema_version": 1,
        "consumption_receipt_ref": receipt_ref,
        "consumption_receipt": receipt,
    }


def _normalize_revision_consumption_receipt(
    value: Any,
    field: str,
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "receipt_kind",
            "schema_version",
            "owner",
            "authority_role",
            "mission_identity",
            "generation_id",
            "producer_attempt_ref",
            "producer_output_ref",
            "applicability",
            "revision_intake_refs",
            "opl_review_receipt_ref",
            "opl_finding_lineage",
            "finding_closures",
            "consumed_revision_refs",
            "authority_boundary",
            "receipt_id",
            "receipt_size_bytes",
            "receipt_fingerprint",
        },
        field,
    )
    if payload.get("receipt_kind") != "mas_revision_consumption_receipt":
        raise RequestShapeError(
            f"{field}.receipt_kind must be mas_revision_consumption_receipt"
        )
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 1")
    if payload.get("owner") != "MedAutoScience":
        raise RequestShapeError(f"{field}.owner must be MedAutoScience")
    if payload.get("authority_role") != "revision_consumption_owner":
        raise RequestShapeError(
            f"{field}.authority_role must be revision_consumption_owner"
        )
    mission_field = f"{field}.mission_identity"
    mission_payload = mapping(payload.get("mission_identity"), mission_field)
    exact_keys(
        mission_payload,
        {"program_id", "study_id", "mission_id"},
        mission_field,
    )
    mission_identity = {
        name: text(mission_payload.get(name), f"{mission_field}.{name}")
        for name in ("program_id", "study_id", "mission_id")
    }
    applicability = enum_text(
        payload.get("applicability"),
        f"{field}.applicability",
        {"not_applicable", "revision_consumed"},
    )
    revision_intake_refs = _exact_ref_list(
        payload.get("revision_intake_refs"),
        f"{field}.revision_intake_refs",
        "opl_revision_intake",
    )
    revision_intake_refs.sort(key=_exact_ref_identity)
    opl_review_receipt_ref = None
    if payload.get("opl_review_receipt_ref") is not None:
        opl_review_receipt_ref = _exact_ref(
            payload.get("opl_review_receipt_ref"),
            f"{field}.opl_review_receipt_ref",
            "opl_stage_review_receipt",
        )
    finding_lineage = _normalize_opl_finding_lineage(
        payload.get("opl_finding_lineage"),
        f"{field}.opl_finding_lineage",
    )
    finding_closures = _normalize_revision_finding_closures(
        payload.get("finding_closures"),
        f"{field}.finding_closures",
    )
    consumed_revision_refs = _normalize_consumed_revision_refs(
        payload.get("consumed_revision_refs"),
        f"{field}.consumed_revision_refs",
    )
    authority_boundary = mapping(
        payload.get("authority_boundary"), f"{field}.authority_boundary"
    )
    exact_keys(
        authority_boundary,
        set(_REVISION_CONSUMPTION_AUTHORITY_BOUNDARY),
        f"{field}.authority_boundary",
    )
    if authority_boundary != _REVISION_CONSUMPTION_AUTHORITY_BOUNDARY:
        raise RequestShapeError(
            f"{field}.authority_boundary must preserve the non-authoritative receipt boundary"
        )

    if applicability == "not_applicable":
        if any(
            (
                revision_intake_refs,
                opl_review_receipt_ref is not None,
                finding_lineage is not None,
                finding_closures,
                consumed_revision_refs,
            )
        ):
            raise RequestShapeError(
                f"{field} not_applicable receipt cannot carry revision inputs or findings"
            )
    else:
        if not revision_intake_refs:
            raise RequestShapeError(
                f"{field}.revision_intake_refs must not be empty when revision is consumed"
            )
        if opl_review_receipt_ref is None or finding_lineage is None:
            raise RequestShapeError(
                f"{field}.opl_review_receipt_ref and opl_finding_lineage are required "
                "when revision is consumed"
            )
        expected_consumed_refs = list(revision_intake_refs)
        if opl_review_receipt_ref is not None:
            expected_consumed_refs.append(opl_review_receipt_ref)
        expected_consumed_refs.sort(
            key=lambda item: (item["kind"], *_exact_ref_identity(item))
        )
        if consumed_revision_refs != expected_consumed_refs:
            raise RequestShapeError(
                f"{field}.consumed_revision_refs must exactly equal revision intake "
                "and review receipt refs"
            )
        if finding_lineage["review_kind"] != "finding_closure_review":
            raise RequestShapeError(
                f"{field}.opl_finding_lineage must be a finding_closure_review"
            )
        finding_ids = set(finding_lineage["finding_ids"])
        closure_ids = {item["finding_id"] for item in finding_closures}
        if finding_ids != closure_ids:
            raise RequestShapeError(
                f"{field}.finding_closures must cover every OPL finding_lineage id "
                "exactly once"
            )

    core = {
        "receipt_kind": "mas_revision_consumption_receipt",
        "schema_version": 1,
        "owner": "MedAutoScience",
        "authority_role": "revision_consumption_owner",
        "mission_identity": mission_identity,
        "generation_id": text(payload.get("generation_id"), f"{field}.generation_id"),
        "producer_attempt_ref": _typed_ref(
            payload.get("producer_attempt_ref"),
            f"{field}.producer_attempt_ref",
            "opl_stage_attempt",
        ),
        "producer_output_ref": _exact_ref(
            payload.get("producer_output_ref"),
            f"{field}.producer_output_ref",
            "opl_action_output",
        ),
        "applicability": applicability,
        "revision_intake_refs": revision_intake_refs,
        "opl_review_receipt_ref": opl_review_receipt_ref,
        "opl_finding_lineage": finding_lineage,
        "finding_closures": finding_closures,
        "consumed_revision_refs": consumed_revision_refs,
        "authority_boundary": dict(_REVISION_CONSUMPTION_AUTHORITY_BOUNDARY),
    }
    expected_fingerprint = fingerprint(core)
    expected_size = len(canonical_json_bytes(core))
    expected_id = (
        f"mas-revision-consumption:{expected_fingerprint.removeprefix('sha256:')}"
    )
    if text(payload.get("receipt_id"), f"{field}.receipt_id") != expected_id:
        raise RequestShapeError(f"{field}.receipt_id does not match canonical receipt")
    if (
        integer(payload.get("receipt_size_bytes"), f"{field}.receipt_size_bytes")
        != expected_size
    ):
        raise RequestShapeError(
            f"{field}.receipt_size_bytes does not match canonical receipt"
        )
    supplied_fingerprint = sha256(
        payload.get("receipt_fingerprint"), f"{field}.receipt_fingerprint"
    )
    if supplied_fingerprint != expected_fingerprint:
        raise RequestShapeError(
            f"{field}.receipt_fingerprint does not match canonical receipt"
        )
    return {
        **core,
        "receipt_id": expected_id,
        "receipt_size_bytes": expected_size,
        "receipt_fingerprint": expected_fingerprint,
    }


def _normalize_opl_finding_lineage(
    value: Any,
    field: str,
) -> dict[str, Any] | None:
    if value is None:
        return None
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "review_kind",
            "finding_ids",
            "findings_sha256",
            "repair_map_sha256",
            "re_review_result_sha256",
        },
        field,
    )
    finding_ids = text_list(payload.get("finding_ids"), f"{field}.finding_ids")
    if not finding_ids:
        raise RequestShapeError(f"{field}.finding_ids must not be empty")
    finding_ids.sort()
    review_kind = enum_text(
        payload.get("review_kind"),
        f"{field}.review_kind",
        {"initial_review", "finding_closure_review"},
    )
    repair_map_sha256 = optional_sha256(
        payload.get("repair_map_sha256"), f"{field}.repair_map_sha256"
    )
    re_review_result_sha256 = optional_sha256(
        payload.get("re_review_result_sha256"),
        f"{field}.re_review_result_sha256",
    )
    if review_kind == "initial_review" and (
        repair_map_sha256 is not None or re_review_result_sha256 is not None
    ):
        raise RequestShapeError(
            f"{field} initial_review must not carry repair or re-review hashes"
        )
    if review_kind == "finding_closure_review" and (
        repair_map_sha256 is None or re_review_result_sha256 is None
    ):
        raise RequestShapeError(
            f"{field} finding_closure_review requires repair_map_sha256 and "
            "re_review_result_sha256"
        )
    return {
        "review_kind": review_kind,
        "finding_ids": finding_ids,
        "findings_sha256": sha256(
            payload.get("findings_sha256"), f"{field}.findings_sha256"
        ),
        "repair_map_sha256": repair_map_sha256,
        "re_review_result_sha256": re_review_result_sha256,
    }


def _normalize_revision_finding_closures(
    value: Any,
    field: str,
) -> list[dict[str, Any]]:
    closures: list[dict[str, Any]] = []
    for index, item in enumerate(sequence(value, field)):
        item_field = f"{field}[{index}]"
        payload = mapping(item, item_field)
        exact_keys(payload, {"finding_id", "status", "evidence_refs"}, item_field)
        evidence_refs = text_list(
            payload.get("evidence_refs"), f"{item_field}.evidence_refs"
        )
        if not evidence_refs:
            raise RequestShapeError(f"{item_field}.evidence_refs must not be empty")
        evidence_refs.sort()
        closures.append(
            {
                "finding_id": text(
                    payload.get("finding_id"), f"{item_field}.finding_id"
                ),
                "status": enum_text(
                    payload.get("status"),
                    f"{item_field}.status",
                    {"closed", "partially_closed", "still_open"},
                ),
                "evidence_refs": evidence_refs,
            }
        )
    finding_ids = [item["finding_id"] for item in closures]
    if len(finding_ids) != len(set(finding_ids)):
        raise RequestShapeError(f"{field} contains duplicate finding_id values")
    closures.sort(key=lambda item: item["finding_id"])
    return closures


def _normalize_consumed_revision_refs(
    value: Any,
    field: str,
) -> list[dict[str, Any]]:
    refs = []
    for index, item in enumerate(sequence(value, field)):
        item_field = f"{field}[{index}]"
        payload = mapping(item, item_field)
        kind = text(payload.get("kind"), f"{item_field}.kind")
        if kind not in {"opl_revision_intake", "opl_stage_review_receipt"}:
            raise RequestShapeError(
                f"{item_field}.kind must be opl_revision_intake or opl_stage_review_receipt"
            )
        refs.append(_exact_ref(payload, item_field, kind))
    identities = [(item["kind"], *_exact_ref_identity(item)) for item in refs]
    if len(identities) != len(set(identities)):
        raise RequestShapeError(f"{field} contains duplicate refs")
    refs.sort(key=lambda item: (item["kind"], *_exact_ref_identity(item)))
    return refs


def _normalize_review_authority(value: Any) -> dict[str, Any]:
    field = "review_authority"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {"review_request_ref", "currentness_receipt_ref", "currentness_receipt"},
        field,
    )
    return {
        "review_request_ref": _exact_ref(
            payload.get("review_request_ref"),
            f"{field}.review_request_ref",
            "opl_action_output",
        ),
        "currentness_receipt_ref": _exact_ref(
            payload.get("currentness_receipt_ref"),
            f"{field}.currentness_receipt_ref",
            "mas_review_currentness_receipt",
        ),
        "currentness_receipt": _normalize_review_currentness_receipt(
            payload.get("currentness_receipt")
        ),
    }


def _normalize_review_currentness_receipt(value: Any) -> dict[str, Any]:
    field = "review_authority.currentness_receipt"
    payload = mapping(value, field)
    schema_version = integer(payload.get("schema_version"), f"{field}.schema_version")
    if schema_version == 1:
        return _normalize_review_currentness_receipt_v1(value)
    if schema_version == 2:
        return _normalize_review_currentness_receipt_v2(value)
    raise RequestShapeError(f"{field}.schema_version must be integer 1 or 2")


def _normalize_review_currentness_receipt_v1(value: Any) -> dict[str, Any]:
    field = "review_authority.currentness_receipt"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "receipt_kind",
            "schema_version",
            "owner",
            "authority_role",
            "authority_epoch",
            "current_generation_id",
            "current_generation_manifest_ref",
            "current_review_request_ref",
            "current_candidate_admission_receipt_refs",
            "current_review_receipt_refs",
            "superseded_generation_ids",
            "superseded_review_request_refs",
            "receipt_id",
            "receipt_size_bytes",
            "receipt_fingerprint",
        },
        field,
    )
    if payload.get("receipt_kind") != "mas_review_currentness_receipt":
        raise RequestShapeError(
            f"{field}.receipt_kind must be mas_review_currentness_receipt"
        )
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 1")
    if payload.get("owner") != "MedAutoScience":
        raise RequestShapeError(f"{field}.owner must be MedAutoScience")
    if payload.get("authority_role") != "review_currentness_owner":
        raise RequestShapeError(
            f"{field}.authority_role must be review_currentness_owner"
        )
    core = {
        "receipt_kind": "mas_review_currentness_receipt",
        "schema_version": 1,
        "owner": "MedAutoScience",
        "authority_role": "review_currentness_owner",
        "authority_epoch": text(
            payload.get("authority_epoch"), f"{field}.authority_epoch"
        ),
        "current_generation_id": text(
            payload.get("current_generation_id"),
            f"{field}.current_generation_id",
        ),
        "current_generation_manifest_ref": _exact_ref(
            payload.get("current_generation_manifest_ref"),
            f"{field}.current_generation_manifest_ref",
            "mas_generation_manifest",
        ),
        "current_review_request_ref": _exact_ref(
            payload.get("current_review_request_ref"),
            f"{field}.current_review_request_ref",
            "opl_action_output",
        ),
        "current_candidate_admission_receipt_refs": _exact_ref_list(
            payload.get("current_candidate_admission_receipt_refs"),
            f"{field}.current_candidate_admission_receipt_refs",
            "mas_candidate_admission_receipt",
        ),
        "current_review_receipt_refs": _exact_ref_list(
            payload.get("current_review_receipt_refs"),
            f"{field}.current_review_receipt_refs",
            "mas_reviewer_receipt",
        ),
        "superseded_generation_ids": text_list(
            payload.get("superseded_generation_ids"),
            f"{field}.superseded_generation_ids",
        ),
        "superseded_review_request_refs": _exact_ref_list(
            payload.get("superseded_review_request_refs"),
            f"{field}.superseded_review_request_refs",
            "opl_action_output",
        ),
    }
    expected_fingerprint = fingerprint(core)
    expected_size = len(canonical_json_bytes(core))
    expected_id = (
        f"mas-review-currentness:{expected_fingerprint.removeprefix('sha256:')}"
    )
    if text(payload.get("receipt_id"), f"{field}.receipt_id") != expected_id:
        raise RequestShapeError(f"{field}.receipt_id does not match canonical receipt")
    if (
        integer(payload.get("receipt_size_bytes"), f"{field}.receipt_size_bytes")
        != expected_size
    ):
        raise RequestShapeError(
            f"{field}.receipt_size_bytes does not match canonical receipt"
        )
    if (
        sha256(payload.get("receipt_fingerprint"), f"{field}.receipt_fingerprint")
        != expected_fingerprint
    ):
        raise RequestShapeError(
            f"{field}.receipt_fingerprint does not match canonical receipt"
        )
    return {
        **core,
        "receipt_id": expected_id,
        "receipt_size_bytes": expected_size,
        "receipt_fingerprint": expected_fingerprint,
    }


def _normalize_review_currentness_receipt_v2(value: Any) -> dict[str, Any]:
    field = "review_authority.currentness_receipt"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "receipt_kind",
            "schema_version",
            "owner",
            "authority_role",
            "authority_epoch",
            "current_generation_id",
            "current_generation_manifest_ref",
            "current_review_request_ref",
            "current_candidate_admission_receipt_refs",
            "lane_currentness",
            "receipt_id",
            "receipt_size_bytes",
            "receipt_fingerprint",
        },
        field,
    )
    if payload.get("receipt_kind") != "mas_review_currentness_receipt":
        raise RequestShapeError(
            f"{field}.receipt_kind must be mas_review_currentness_receipt"
        )
    if payload.get("schema_version") != 2 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 2")
    if payload.get("owner") != "MedAutoScience":
        raise RequestShapeError(f"{field}.owner must be MedAutoScience")
    if payload.get("authority_role") != "review_currentness_owner":
        raise RequestShapeError(
            f"{field}.authority_role must be review_currentness_owner"
        )
    lanes = [
        _normalize_lane_currentness(
            item,
            f"{field}.lane_currentness[{index}]",
        )
        for index, item in enumerate(
            sequence(payload.get("lane_currentness"), f"{field}.lane_currentness")
        )
    ]
    lane_ids = [item["review_lane"] for item in lanes]
    if len(lane_ids) != len(set(lane_ids)):
        raise RequestShapeError(f"{field}.lane_currentness contains duplicate lanes")
    lanes.sort(key=lambda item: item["review_lane"])
    core = {
        "receipt_kind": "mas_review_currentness_receipt",
        "schema_version": 2,
        "owner": "MedAutoScience",
        "authority_role": "review_currentness_owner",
        "authority_epoch": text(
            payload.get("authority_epoch"), f"{field}.authority_epoch"
        ),
        "current_generation_id": text(
            payload.get("current_generation_id"),
            f"{field}.current_generation_id",
        ),
        "current_generation_manifest_ref": _exact_ref(
            payload.get("current_generation_manifest_ref"),
            f"{field}.current_generation_manifest_ref",
            "mas_generation_manifest",
        ),
        "current_review_request_ref": _exact_ref(
            payload.get("current_review_request_ref"),
            f"{field}.current_review_request_ref",
            "opl_action_output",
        ),
        "current_candidate_admission_receipt_refs": _exact_ref_list(
            payload.get("current_candidate_admission_receipt_refs"),
            f"{field}.current_candidate_admission_receipt_refs",
            "mas_candidate_admission_receipt",
        ),
        "lane_currentness": lanes,
    }
    expected_fingerprint = fingerprint(core)
    expected_size = len(canonical_json_bytes(core))
    expected_id = (
        f"mas-review-currentness:{expected_fingerprint.removeprefix('sha256:')}"
    )
    if text(payload.get("receipt_id"), f"{field}.receipt_id") != expected_id:
        raise RequestShapeError(f"{field}.receipt_id does not match canonical receipt")
    if (
        integer(payload.get("receipt_size_bytes"), f"{field}.receipt_size_bytes")
        != expected_size
    ):
        raise RequestShapeError(
            f"{field}.receipt_size_bytes does not match canonical receipt"
        )
    if (
        sha256(payload.get("receipt_fingerprint"), f"{field}.receipt_fingerprint")
        != expected_fingerprint
    ):
        raise RequestShapeError(
            f"{field}.receipt_fingerprint does not match canonical receipt"
        )
    return {
        **core,
        "receipt_id": expected_id,
        "receipt_size_bytes": expected_size,
        "receipt_fingerprint": expected_fingerprint,
    }


def _normalize_lane_currentness(value: Any, field: str) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "review_lane",
            "review_authority_epoch",
            "currentness_status",
            "current_rubric_ref",
            "review_scope_sha256",
            "review_receipt_issued_generation_id",
            "review_receipt_issued_generation_manifest_sha256",
            "current_review_request_ref",
            "current_review_receipt_ref",
            "superseded_review_request_refs",
            "reuse_provenance",
            "epistemic_currentness",
        },
        field,
    )
    lane = enum_text(
        payload.get("review_lane"),
        f"{field}.review_lane",
        set().union(*REVIEW_LANES_BY_SCOPE.values()),
    )
    status = enum_text(
        payload.get("currentness_status"),
        f"{field}.currentness_status",
        {"fresh", "reused_unchanged_scope"},
    )
    reuse_value = payload.get("reuse_provenance")
    reuse = None
    if status == "fresh":
        if reuse_value is not None:
            raise RequestShapeError(
                f"{field}.reuse_provenance must be null for fresh review"
            )
    else:
        reuse = _normalize_reuse_provenance(reuse_value, f"{field}.reuse_provenance")
    return {
        "review_lane": lane,
        "review_authority_epoch": text(
            payload.get("review_authority_epoch"),
            f"{field}.review_authority_epoch",
        ),
        "currentness_status": status,
        "current_rubric_ref": _typed_ref(
            payload.get("current_rubric_ref"),
            f"{field}.current_rubric_ref",
            "mas_quality_rubric",
        ),
        "review_scope_sha256": sha256(
            payload.get("review_scope_sha256"),
            f"{field}.review_scope_sha256",
        ),
        "review_receipt_issued_generation_id": text(
            payload.get("review_receipt_issued_generation_id"),
            f"{field}.review_receipt_issued_generation_id",
        ),
        "review_receipt_issued_generation_manifest_sha256": sha256(
            payload.get("review_receipt_issued_generation_manifest_sha256"),
            f"{field}.review_receipt_issued_generation_manifest_sha256",
        ),
        "current_review_request_ref": _exact_ref(
            payload.get("current_review_request_ref"),
            f"{field}.current_review_request_ref",
            "opl_action_output",
        ),
        "current_review_receipt_ref": _exact_ref(
            payload.get("current_review_receipt_ref"),
            f"{field}.current_review_receipt_ref",
            "mas_reviewer_receipt",
        ),
        "superseded_review_request_refs": _exact_ref_list(
            payload.get("superseded_review_request_refs"),
            f"{field}.superseded_review_request_refs",
            "opl_action_output",
        ),
        "reuse_provenance": reuse,
        "epistemic_currentness": _normalize_epistemic_currentness(
            payload.get("epistemic_currentness"),
            f"{field}.epistemic_currentness",
            lane=lane,
        ),
    }


def _normalize_epistemic_currentness(
    value: Any,
    field: str,
    *,
    lane: str,
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "surface_kind",
            "version",
            "scope_id",
            "scope_kind",
            "status",
            "invalidating_changes",
            "ignored_changes",
            "reviewed_dependency_refs",
            "authority_boundary",
        },
        field,
    )
    if payload.get("surface_kind") != "opl_epistemic_review_currentness_evaluation":
        raise RequestShapeError(
            f"{field}.surface_kind must be opl_epistemic_review_currentness_evaluation"
        )
    if payload.get("version") != "opl-epistemic-review-currentness-evaluation.v2":
        raise RequestShapeError(
            f"{field}.version must be opl-epistemic-review-currentness-evaluation.v2"
        )
    scope_id = text(payload.get("scope_id"), f"{field}.scope_id")
    if scope_id != f"mas:{lane}":
        raise RequestShapeError(f"{field}.scope_id must be mas:{lane}")
    status = enum_text(
        payload.get("status"), f"{field}.status", {"current", "stale"}
    )
    invalidating = [
        _normalize_epistemic_change(item, f"{field}.invalidating_changes[{index}]")
        for index, item in enumerate(
            sequence(payload.get("invalidating_changes"), f"{field}.invalidating_changes")
        )
    ]
    ignored = [
        _normalize_epistemic_change(
            item,
            f"{field}.ignored_changes[{index}]",
            ignored=True,
        )
        for index, item in enumerate(
            sequence(payload.get("ignored_changes"), f"{field}.ignored_changes")
        )
    ]
    if (status == "current" and invalidating) or (
        status == "stale" and not invalidating
    ):
        raise RequestShapeError(
            f"{field}.status must agree with invalidating_changes"
        )
    dependency_refs = text_list(
        payload.get("reviewed_dependency_refs"),
        f"{field}.reviewed_dependency_refs",
    )
    if not dependency_refs or dependency_refs != sorted(set(dependency_refs)):
        raise RequestShapeError(
            f"{field}.reviewed_dependency_refs must be sorted and unique"
        )
    authority = mapping(payload.get("authority_boundary"), f"{field}.authority_boundary")
    exact_keys(
        authority,
        set(EPISTEMIC_AUTHORITY_BOUNDARY),
        f"{field}.authority_boundary",
    )
    if authority != EPISTEMIC_AUTHORITY_BOUNDARY:
        raise RequestShapeError(
            f"{field}.authority_boundary must preserve the OPL/MAS authority split"
        )
    return {
        "surface_kind": "opl_epistemic_review_currentness_evaluation",
        "version": "opl-epistemic-review-currentness-evaluation.v2",
        "scope_id": scope_id,
        "scope_kind": enum_text(
            payload.get("scope_kind"),
            f"{field}.scope_kind",
            {"content", "reference", "display", "package"},
        ),
        "status": status,
        "invalidating_changes": invalidating,
        "ignored_changes": ignored,
        "reviewed_dependency_refs": dependency_refs,
        "authority_boundary": dict(EPISTEMIC_AUTHORITY_BOUNDARY),
    }


def _normalize_epistemic_change(
    value: Any,
    field: str,
    *,
    ignored: bool = False,
) -> dict[str, Any]:
    payload = mapping(value, field)
    keys = {
        "node_ref",
        "change_class",
        "semantic_changed",
        "locator_sha256_before",
        "locator_sha256_after",
    }
    if ignored:
        keys.add("reason")
    exact_keys(payload, keys, field)
    if not isinstance(payload.get("semantic_changed"), bool):
        raise RequestShapeError(f"{field}.semantic_changed must be boolean")
    if not ignored and payload["semantic_changed"] is not True:
        raise RequestShapeError(
            f"{field}.semantic_changed must be true for an invalidating change"
        )
    normalized = {
        "node_ref": text(payload.get("node_ref"), f"{field}.node_ref"),
        "change_class": enum_text(
            payload.get("change_class"),
            f"{field}.change_class",
            _EPISTEMIC_CHANGE_CLASSES,
        ),
        "semantic_changed": payload["semantic_changed"],
        "locator_sha256_before": optional_sha256(
            payload.get("locator_sha256_before"),
            f"{field}.locator_sha256_before",
        ),
        "locator_sha256_after": optional_sha256(
            payload.get("locator_sha256_after"),
            f"{field}.locator_sha256_after",
        ),
    }
    if ignored:
        normalized["reason"] = enum_text(
            payload.get("reason"),
            f"{field}.reason",
            _EPISTEMIC_IGNORED_REASONS,
        )
    return normalized


def _normalize_reuse_provenance(value: Any, field: str) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "origin_generation_id",
            "origin_generation_manifest_ref",
            "origin_review_request_ref",
            "origin_review_receipt_ref",
            "origin_review_scope_sha256",
            "origin_candidate_admission_receipt_refs",
        },
        field,
    )
    return {
        "origin_generation_id": text(
            payload.get("origin_generation_id"), f"{field}.origin_generation_id"
        ),
        "origin_generation_manifest_ref": _exact_ref(
            payload.get("origin_generation_manifest_ref"),
            f"{field}.origin_generation_manifest_ref",
            "mas_generation_manifest",
        ),
        "origin_review_request_ref": _exact_ref(
            payload.get("origin_review_request_ref"),
            f"{field}.origin_review_request_ref",
            "opl_action_output",
        ),
        "origin_review_receipt_ref": _exact_ref(
            payload.get("origin_review_receipt_ref"),
            f"{field}.origin_review_receipt_ref",
            "mas_reviewer_receipt",
        ),
        "origin_review_scope_sha256": sha256(
            payload.get("origin_review_scope_sha256"),
            f"{field}.origin_review_scope_sha256",
        ),
        "origin_candidate_admission_receipt_refs": _exact_ref_list(
            payload.get("origin_candidate_admission_receipt_refs"),
            f"{field}.origin_candidate_admission_receipt_refs",
            "mas_candidate_admission_receipt",
        ),
    }


def _normalize_repair(value: Any) -> dict[str, Any]:
    field = "repair_state"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "status",
            "attempts_used",
            "max_attempts",
            "repair_attempt_refs",
            "latest_repair_output_ref",
        },
        field,
    )
    attempts_used = integer(payload.get("attempts_used"), f"{field}.attempts_used")
    max_attempts = integer(payload.get("max_attempts"), f"{field}.max_attempts")
    if max_attempts != 3:
        raise RequestShapeError(
            "repair_state.max_attempts must equal the OPL scope budget of 3"
        )
    if attempts_used > max_attempts:
        raise RequestShapeError("repair_state.attempts_used cannot exceed max_attempts")
    attempt_refs = _typed_ref_list(
        payload.get("repair_attempt_refs"),
        f"{field}.repair_attempt_refs",
        "opl_stage_attempt",
    )
    if len(attempt_refs) != attempts_used:
        raise RequestShapeError("repair_attempt_refs must exactly match attempts_used")
    return {
        "status": enum_text(
            payload.get("status"),
            f"{field}.status",
            {"not_required", "pending", "completed", "exhausted", "failed"},
        ),
        "attempts_used": attempts_used,
        "max_attempts": max_attempts,
        "repair_attempt_refs": attempt_refs,
        "latest_repair_output_ref": _optional_typed_ref(
            payload.get("latest_repair_output_ref"),
            f"{field}.latest_repair_output_ref",
            "opl_action_output",
        ),
    }


def _normalize_hard_gate(value: Any) -> dict[str, Any]:
    field = "hard_gate"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {"kind", "reason_code", "evidence_refs", "next_owner", "resume_condition"},
        field,
    )
    kind = enum_text(
        payload.get("kind"),
        f"{field}.kind",
        {"none", "human_decision", *_HARD_GATE_KINDS},
    )
    normalized = {
        "kind": kind,
        "reason_code": optional_text(
            payload.get("reason_code"), f"{field}.reason_code"
        ),
        "evidence_refs": _typed_ref_list(
            payload.get("evidence_refs"),
            f"{field}.evidence_refs",
            "mas_gate_evidence",
        ),
        "next_owner": optional_text(payload.get("next_owner"), f"{field}.next_owner"),
        "resume_condition": optional_text(
            payload.get("resume_condition"), f"{field}.resume_condition"
        ),
    }
    if kind == "none":
        if any(
            (
                normalized["reason_code"] is not None,
                bool(normalized["evidence_refs"]),
                normalized["next_owner"] is not None,
                normalized["resume_condition"] is not None,
            )
        ):
            raise RequestShapeError("hard_gate.kind none requires an empty gate record")
        return normalized
    missing = [
        name
        for name in ("reason_code", "next_owner", "resume_condition")
        if normalized[name] is None
    ]
    if not normalized["evidence_refs"]:
        missing.append("evidence_refs")
    if missing:
        raise RequestShapeError("hard gate missing: " + ", ".join(missing))
    return normalized


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
            expected_snapshot_generation_ref = (
                manifest_ref["ref"]
                if lane_state["currentness_status"] == "fresh"
                else (
                    reuse_provenance["origin_generation_manifest_ref"]["ref"]
                    if reuse_provenance is not None
                    else None
                )
            )
            snapshot_binding = receipt.get("review_input_snapshot_binding")
            if snapshot_binding is None:
                lane_issue = (
                    "review_input_snapshot_binding_required",
                    f"obtain a fresh {lane} review over the immutable input snapshot",
                )
            elif (
                snapshot_binding.get("generation_ref") is None
                or snapshot_binding.get("mas_authority_record_ref") is None
                or snapshot_binding.get("materialization_owner") != "one-person-lab"
                or snapshot_binding.get("authority_boundary")
                != _SNAPSHOT_AUTHORITY_BOUNDARY
            ):
                lane_issue = (
                    "review_input_snapshot_binding_owner_metadata_required",
                    f"refresh {lane} snapshot binding with its generation/authority "
                    "identity, transport owner, and false-authority boundary",
                )
            elif any(
                (
                    (
                        expected_snapshot_generation_ref is not None
                        and snapshot_binding["generation_ref"]
                        != expected_snapshot_generation_ref
                    ),
                    snapshot_binding["review_lane"] != lane,
                    snapshot_binding["review_scope_sha256"]
                    != receipt["review_scope_sha256"],
                    snapshot_binding["members"]
                    != review_scope_member_projection(receipt["reviewed_members"]),
                )
            ):
                lane_issue = (
                    "review_input_snapshot_binding_not_current",
                    f"refresh {lane} review against the complete immutable snapshot inventory",
                )
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
    receipt = binding["consumption_receipt"]
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


def _aggregate_review_status(request: Mapping[str, Any]) -> str:
    verdicts = {
        item["receipt"]["verdict"]
        for item in request["generation_manifest"]["independent_review_receipts"]
    }
    if "rejected" in verdicts:
        return "rejected"
    if "revision_required" in verdicts:
        return "revision_required"
    return "passed"


def _review_quality_debt(
    request: Mapping[str, Any],
) -> tuple[list[str], list[dict[str, str]]]:
    codes: list[str] = []
    refs: list[dict[str, str]] = []
    for wrapper in request["generation_manifest"]["independent_review_receipts"]:
        receipt = wrapper["receipt"]
        codes.extend(receipt["quality_debt_codes"])
        refs.extend(receipt["defect_refs"])
    unique_refs = {(item["ref"], item["sha256"]): item for item in refs}
    return dedupe(codes), list(unique_refs.values())


def _professional_figure_skill_quality_debt(
    request: Mapping[str, Any],
) -> list[str]:
    manifest = request["generation_manifest"]
    figure_artifacts = {
        item["member_id"]: item
        for item in manifest["artifacts"]
        if item["role"] == "figure_file" and "member_id" in item
    }
    if not figure_artifacts:
        return []

    invocations = [
        item
        for item in manifest.get("professional_skill_invocations", [])
        if item["surface_kind"] == "mas_professional_figure_skill_invocation_candidate"
    ]
    if not invocations:
        return ["professional_figure_skill_consumption_evidence_missing"]

    groups: dict[str, list[Mapping[str, Any]]] = {}
    for invocation in invocations:
        groups.setdefault(invocation["figure_id"], []).append(invocation)

    codes: list[str] = []
    covered_members: set[str] = set()
    for figure_id, group in sorted(groups.items()):
        skills = {item["skill_id"] for item in group}
        required = {"medical-figure-design", "medical-figure-style"}
        composition_modes = {item["composition_mode"] for item in group}
        figure_kinds = {item["figure_kind"] for item in group}
        if len(composition_modes) != 1 or len(figure_kinds) != 1:
            codes.append("professional_figure_skill_receipt_scope_mismatch")
            continue
        if composition_modes == {"assembled_panels"}:
            required.add("medical-figure-composer")
        missing = required - skills
        if "medical-figure-design" in missing:
            codes.append("professional_figure_design_consumption_missing")
        if "medical-figure-style" in missing:
            codes.append("professional_figure_style_consumption_missing")
        if "medical-figure-composer" in missing:
            codes.append("professional_figure_composer_consumption_missing")
        unexpected_composer = (
            composition_modes == {"single_canvas_direct"}
            and "medical-figure-composer" in skills
        )
        if unexpected_composer:
            codes.append("professional_figure_composer_receipt_not_applicable")

        output_sets = {
            tuple(
                sorted(
                    binding["member_id"] for binding in item["output_artifact_bindings"]
                )
            )
            for item in group
        }
        if len(output_sets) != 1:
            codes.append("professional_figure_skill_output_binding_mismatch")
            continue
        member_ids = set(next(iter(output_sets)))
        if not member_ids.issubset(figure_artifacts):
            codes.append("professional_figure_skill_output_binding_invalid")
            continue
        if any(
            binding
            != {
                key: figure_artifacts[binding["member_id"]][key]
                for key in ("member_id", "role", "ref", "size_bytes", "sha256")
            }
            for item in group
            for binding in item["output_artifact_bindings"]
        ):
            codes.append("professional_figure_skill_output_binding_stale")
        covered_members.update(member_ids)
        if not figure_id.strip():
            codes.append("professional_figure_skill_figure_identity_missing")

    if covered_members != set(figure_artifacts):
        codes.append("professional_figure_skill_output_coverage_incomplete")
    return dedupe(codes)


def _professional_manuscript_skill_quality_debt(
    request: Mapping[str, Any],
) -> list[str]:
    manifest = request["generation_manifest"]
    if manifest["schema_version"] != 2 or manifest["manifest_scope"] == (
        "analysis_generation"
    ):
        return []
    artifacts = {
        item["member_id"]: item for item in manifest["artifacts"] if "member_id" in item
    }
    invocations = [
        item
        for item in manifest.get("professional_skill_invocations", [])
        if item["surface_kind"]
        == ("mas_professional_manuscript_skill_invocation_candidate")
    ]
    invocations_by_skill = {item["skill_id"]: item for item in invocations}
    artifact_roles = {item["role"] for item in artifacts.values()}
    required_skills = {"medical-manuscript-writing"}
    if artifact_roles & {"analysis_output", "numeric_trace"}:
        required_skills.add("medical-statistical-review")
    if artifact_roles & {"table_catalog", "table_file"}:
        required_skills.add("medical-table-design")
    if manifest["manifest_scope"] == "publication_generation":
        required_skills.add("medical-submission-prep")
    missing_codes = {
        "medical-manuscript-writing": (
            "professional_manuscript_writing_consumption_missing"
        ),
        "medical-statistical-review": (
            "professional_statistical_review_consumption_missing"
        ),
        "medical-table-design": "professional_table_design_consumption_missing",
        "medical-submission-prep": (
            "professional_submission_prep_consumption_missing"
        ),
    }
    coverage_codes = {
        "medical-manuscript-writing": (
            "professional_manuscript_writing_output_coverage_incomplete"
        ),
        "medical-registry-atlas-story-architect": (
            "professional_registry_story_output_coverage_incomplete"
        ),
        "medical-statistical-review": (
            "professional_statistical_review_output_coverage_incomplete"
        ),
        "medical-table-design": (
            "professional_table_design_output_coverage_incomplete"
        ),
        "medical-submission-prep": (
            "professional_submission_prep_output_coverage_incomplete"
        ),
    }
    codes: list[str] = []
    for skill_id in sorted(required_skills):
        if skill_id not in invocations_by_skill:
            codes.append(missing_codes[skill_id])
    for invocation in invocations:
        allowed_roles = PROFESSIONAL_MANUSCRIPT_SKILL_ROLES[invocation["skill_id"]]
        expected_member_ids = {
            member_id
            for member_id, artifact in artifacts.items()
            if artifact["role"] in allowed_roles
        }
        covered_member_ids = {
            binding["member_id"] for binding in invocation["output_artifact_bindings"]
        }
        if covered_member_ids != expected_member_ids:
            codes.append(coverage_codes[invocation["skill_id"]])
        for binding in invocation["output_artifact_bindings"]:
            expected = artifacts.get(binding["member_id"])
            if (
                expected is None
                or expected["role"] not in allowed_roles
                or any(
                    binding[key] != expected[key]
                    for key in ("member_id", "role", "ref", "size_bytes", "sha256")
                )
            ):
                codes.append("professional_manuscript_skill_output_binding_stale")
    return dedupe(codes)


def _professional_skill_debt_result(
    request: Mapping[str, Any],
    *,
    reason_codes: list[str],
    resume_condition: str,
) -> dict[str, Any]:
    reason_code = reason_codes[0]
    if request["mission"]["stage_id"] == "finalize_and_publication_handoff":
        return _route_result(
            request,
            reason_code=reason_code,
            next_owner="mission_executor",
            resume_condition=resume_condition,
        )
    route_back = _route_back(
        request,
        reason_code=reason_code,
        next_owner="mission_executor",
        resume_condition=resume_condition,
    )
    return _finalize(
        request,
        status="completed_with_quality_debt",
        stage_outcome=_stage_outcome(
            "completed_with_quality_debt", transition_allowed=True
        ),
        route_back=route_back,
        quality_debt=_quality_debt(request, reason_codes=reason_codes),
    )


def _owner_receipt(request: Mapping[str, Any]) -> dict[str, Any]:
    evidence = request["medical_evidence"]
    reviews = request["generation_manifest"]["independent_review_receipts"]
    currentness = request["review_authority"]["currentness_receipt"]
    core = {
        "receipt_kind": "mas_paper_mission_owner_receipt",
        "schema_version": 2,
        "owner": "MedAutoScience",
        "mission_identity": dict(request["mission"]),
        "host_refs": _host_refs(request),
        "generation_identity": _generation_identity(request),
        "review_authority_epoch": currentness["authority_epoch"],
        "review_currentness_receipt_ref": dict(
            request["review_authority"]["currentness_receipt_ref"]
        ),
        "accepted_candidate_admissions": [
            {
                "candidate_id": item["receipt"]["candidate_id"],
                "candidate_ref": dict(item["receipt"]["candidate_ref"]),
                "receipt_ref": dict(item["receipt_ref"]),
                "claim_scope": dict(item["receipt"]["claim_scope"]),
            }
            for item in request["candidate_admissions"]
        ],
        "medical_evidence_refs": list(evidence["evidence_refs"]),
        "negative_result_refs": list(evidence["negative_result_refs"]),
        "failed_path_refs": list(evidence["failed_path_refs"]),
        "artifact_lineage_refs": list(evidence["artifact_lineage_refs"]),
        "reproducibility_refs": list(evidence["reproducibility_refs"]),
        "source_readiness_receipt_ref": evidence["source_readiness_receipt_ref"],
        "claim_boundary_ref": evidence["claim_boundary_ref"],
        "independent_review_receipt_refs": [
            dict(item["receipt_ref"]) for item in reviews
        ],
        "revision_consumption": _revision_consumption_projection(request),
        "verdict": "accepted_domain_delta",
        "authorizes_stage_domain_completion": True,
        "authorizes_publication_or_submission": False,
        "requires_host_exact_byte_persistence": True,
    }
    if request["mission"]["stage_id"] == "finalize_and_publication_handoff":
        core["artifact_projection_transport"] = _artifact_projection_transport(request)
    receipt_fingerprint = fingerprint(core)
    return {
        **core,
        "receipt_id": (
            "mas-paper-mission-owner-receipt:"
            f"{receipt_fingerprint.removeprefix('sha256:')}"
        ),
        "receipt_size_bytes": len(canonical_json_bytes(core)),
        "receipt_fingerprint": receipt_fingerprint,
    }


def _revision_consumption_projection(request: Mapping[str, Any]) -> dict[str, Any]:
    binding = request["revision_consumption"]
    receipt = binding["consumption_receipt"]
    return {
        "surface_kind": "mas_revision_consumption_owner_projection",
        "schema_version": 1,
        "consumption_receipt_ref": dict(binding["consumption_receipt_ref"]),
        "applicability": receipt["applicability"],
        "revision_intake_refs": [
            dict(item) for item in receipt["revision_intake_refs"]
        ],
        "opl_review_receipt_ref": (
            dict(receipt["opl_review_receipt_ref"])
            if receipt["opl_review_receipt_ref"] is not None
            else None
        ),
        "opl_finding_lineage": (
            dict(receipt["opl_finding_lineage"])
            if receipt["opl_finding_lineage"] is not None
            else None
        ),
        "finding_closures": [dict(item) for item in receipt["finding_closures"]],
        "consumed_revision_refs": [
            dict(item) for item in receipt["consumed_revision_refs"]
        ],
        "authority_boundary": dict(receipt["authority_boundary"]),
    }


def _artifact_projection_transport(request: Mapping[str, Any]) -> dict[str, Any]:
    manifest = request["generation_manifest"]
    required_roles = (
        "submission_status",
        "publication_evaluation",
        "next_action_envelope",
        "submission_projection_manifest",
    )
    members = {
        role: next(item for item in manifest["artifacts"] if item["role"] == role)
        for role in required_roles
    }
    return {
        "surface_kind": "mas_artifact_projection_transport_authorization",
        "schema_version": 1,
        "transport_owner": "One Person Lab",
        "transport_action_id": "opl_pack_materialize_artifact_projection",
        "request_contract_ref": (
            "contracts/opl-framework/"
            "artifact-projection-materialization-request.schema.json"
        ),
        "receipt_contract_ref": (
            "contracts/opl-framework/"
            "artifact-projection-materialization-receipt.schema.json"
        ),
        "generation_id": manifest["generation_id"],
        "generation_manifest_ref": dict(request["generation_manifest_ref"]),
        "projection_manifest_ref": _generation_artifact_identity(
            members["submission_projection_manifest"]
        ),
        "generation_bound_truth_members": [
            _generation_artifact_identity(members[role])
            for role in (
                "submission_status",
                "publication_evaluation",
                "next_action_envelope",
            )
        ],
        "target_role": "study_submission_root",
        "completion_marker_paths": [
            "STATUS.json",
            "audit/submission_manifest.json",
        ],
        "opl_request_domain_authorization": {
            "owner": "MedAutoScience",
            "ref_source": "owner_receipt.receipt_id",
            "scope": "artifact_projection_only",
            "artifact_body_write_authorized": True,
            "authorizes_quality_publication_or_submission": False,
        },
        "source_tree_must_match_projection_manifest": True,
        "atomic_tree_switch_required": True,
        "transport_can_write_domain_truth": False,
    }


def _generation_artifact_identity(member: Mapping[str, Any]) -> dict[str, Any]:
    """Project a manifest member onto the stable transport-v1 artifact ABI."""

    return {name: member[name] for name in ("role", "ref", "size_bytes", "sha256")}


def _route_result(
    request: Mapping[str, Any],
    *,
    reason_code: str,
    next_owner: str,
    resume_condition: str,
    affected_review_lanes: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    return _finalize(
        request,
        status="route_back",
        stage_outcome=_stage_outcome("route_back", transition_allowed=False),
        route_back=_route_back(
            request,
            reason_code=reason_code,
            next_owner=next_owner,
            resume_condition=resume_condition,
            affected_review_lanes=affected_review_lanes,
        ),
    )


def _route_back(
    request: Mapping[str, Any],
    *,
    reason_code: str,
    next_owner: str,
    resume_condition: str,
    affected_review_lanes: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    repair = request["repair_state"]
    debt_codes, defect_refs = _review_quality_debt(request)
    route_back = {
        "reason_code": reason_code,
        "next_owner": next_owner,
        "resume_condition": resume_condition,
        "review_verdicts": [
            {
                "review_lane": item["receipt"]["review_lane"],
                "verdict": item["receipt"]["verdict"],
            }
            for item in request["generation_manifest"]["independent_review_receipts"]
        ],
        "quality_debt_codes": debt_codes,
        "defect_refs": defect_refs,
        "repair_attempt_refs": list(repair["repair_attempt_refs"]),
        "remaining_repair_attempts": max(
            repair["max_attempts"] - repair["attempts_used"], 0
        ),
        "selects_next_stage": False,
    }
    if affected_review_lanes is not None:
        route_back["affected_review_lanes"] = [
            dict(item) for item in affected_review_lanes
        ]
    return route_back


def _typed_blocker(request: Mapping[str, Any]) -> dict[str, Any]:
    gate = request["hard_gate"]
    return {
        "blocker_kind": "mas_paper_mission_typed_blocker",
        "gate_kind": gate["kind"],
        "reason_code": gate["reason_code"],
        "evidence_refs": list(gate["evidence_refs"]),
        "next_owner": gate["next_owner"],
        "resume_condition": gate["resume_condition"],
        "blocks_stage_transition": True,
        "requires_host_exact_byte_persistence": True,
    }


def _human_gate(request: Mapping[str, Any]) -> dict[str, Any]:
    gate = request["hard_gate"]
    return {
        "gate_kind": "mas_paper_mission_human_gate",
        "reason_code": gate["reason_code"],
        "evidence_refs": list(gate["evidence_refs"]),
        "next_owner": gate["next_owner"],
        "resume_condition": gate["resume_condition"],
        "blocks_stage_transition": True,
        "requires_host_exact_byte_persistence": True,
    }


def _quality_debt(
    request: Mapping[str, Any], *, reason_codes: list[str]
) -> dict[str, Any]:
    _, defect_refs = _review_quality_debt(request)
    return {
        "reason_codes": reason_codes,
        "review_verdict": _aggregate_review_status(request),
        "defect_refs": defect_refs,
        "transition_allowed": True,
        "blocks_quality_publication_export_and_submission_claims": True,
        "counts_as_owner_acceptance": False,
    }


def _stage_outcome(kind: str, *, transition_allowed: bool) -> dict[str, Any]:
    return {
        "kind": kind,
        "stage_transition_allowed": transition_allowed,
        "selects_next_stage": False,
        "publication_or_submission_ready": False,
    }


def _finalize(
    request: Mapping[str, Any],
    *,
    status: str,
    stage_outcome: Mapping[str, Any],
    owner_receipt: Mapping[str, Any] | None = None,
    route_back: Mapping[str, Any] | None = None,
    typed_blocker: Mapping[str, Any] | None = None,
    human_gate: Mapping[str, Any] | None = None,
    quality_debt: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    core = {
        "surface_kind": RESULT_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "mission_identity": dict(request["mission"]),
        "host_refs": _host_refs(request),
        "generation_identity": _generation_identity(request),
        "stage_outcome": dict(stage_outcome),
        "owner_receipt": dict(owner_receipt) if owner_receipt is not None else None,
        "route_back": dict(route_back) if route_back is not None else None,
        "typed_blocker": dict(typed_blocker) if typed_blocker is not None else None,
        "human_gate": dict(human_gate) if human_gate is not None else None,
        "quality_debt": dict(quality_debt) if quality_debt is not None else None,
        "error": None,
        "authority_boundary": dict(_AUTHORITY_BOUNDARY),
    }
    decision_fingerprint = fingerprint(core)
    return {
        **core,
        "decision_id": (
            "mas-paper-mission-authority:"
            f"{decision_fingerprint.removeprefix('sha256:')}"
        ),
        "decision_fingerprint": decision_fingerprint,
    }


def _invalid_host_input(detail: str) -> dict[str, Any]:
    core = {
        "surface_kind": RESULT_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "invalid_host_input",
        "mission_identity": None,
        "host_refs": None,
        "generation_identity": None,
        "stage_outcome": _stage_outcome("invalid_host_input", transition_allowed=False),
        "owner_receipt": None,
        "route_back": None,
        "typed_blocker": None,
        "human_gate": None,
        "quality_debt": None,
        "error": {"code": "invalid_host_input", "detail": detail},
        "authority_boundary": dict(_AUTHORITY_BOUNDARY),
    }
    decision_fingerprint = fingerprint(core)
    return {
        **core,
        "decision_id": (
            "mas-paper-mission-authority:"
            f"{decision_fingerprint.removeprefix('sha256:')}"
        ),
        "decision_fingerprint": decision_fingerprint,
    }


def _host_refs(request: Mapping[str, Any]) -> dict[str, Any]:
    host = request["host_context"]
    return {
        "run_ref": dict(host["run_ref"]),
        "producer_attempt_ref": dict(host["producer_attempt_ref"]),
        "output_ref": dict(host["output_ref"]),
    }


def _generation_identity(request: Mapping[str, Any]) -> dict[str, Any]:
    manifest = request["generation_manifest"]
    authority = request["review_authority"]
    return {
        "generation_id": manifest["generation_id"],
        "manifest_scope": manifest["manifest_scope"],
        "generation_manifest_ref": dict(request["generation_manifest_ref"]),
        "review_authority_epoch": authority["currentness_receipt"]["authority_epoch"],
        "review_request_ref": dict(authority["review_request_ref"]),
    }


__all__ = ["evaluate_paper_mission_authority"]
