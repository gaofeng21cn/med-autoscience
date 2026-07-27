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
    REQUEST_KIND,
    SCHEMA_VERSION,
    _REVISION_CONSUMPTION_AUTHORITY_BOUNDARY,
)
from .currentness import (
    _normalize_hard_gate,
    _normalize_repair,
    _normalize_review_currentness_receipt,
    _normalize_selected_build_currentness_authority,
)
from .validation import (
    _exact_ref_identity,
    _validate_review_currentness_receipt_ref,
    _validate_selected_build_currentness_authority,
)

def _is_reviewer_revision(request: Mapping[str, Any]) -> bool:
    receipt = request["revision_consumption"]["consumption_receipt"]
    return receipt is not None and receipt["applicability"] == "revision_consumed"


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
    if "selected_build_currentness_authority" in payload:
        request_keys.add("selected_build_currentness_authority")
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
    selected_build = manifest.get("selected_build_binding")
    if selected_build is not None and "selected_build_currentness_authority" not in payload:
        raise RequestShapeError(
            "selected_build_currentness_authority is required for selected build binding"
        )
    if selected_build is None and "selected_build_currentness_authority" in payload:
        raise RequestShapeError(
            "selected_build_currentness_authority requires selected build binding"
        )
    host_context = _normalize_host_context(payload.get("host_context"))
    review_authority = _normalize_review_authority(payload.get("review_authority"))
    selected_build_authority = (
        _normalize_selected_build_currentness_authority(
            payload.get("selected_build_currentness_authority")
        )
        if selected_build is not None
        else None
    )
    normalized = {
        "surface_kind": REQUEST_KIND,
        "schema_version": SCHEMA_VERSION,
        "host_context": host_context,
        "mission": mission,
        "medical_evidence": _normalize_medical_evidence(
            payload.get("medical_evidence")
        ),
        "generation_manifest": manifest,
        "generation_manifest_ref": manifest_ref,
        "candidate_admissions": _normalize_candidate_admissions(
            payload.get("candidate_admissions")
        ),
        "review_authority": review_authority,
        "selected_build_currentness_authority": selected_build_authority,
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
    _validate_selected_build_currentness_authority(normalized)
    return normalized


def _normalize_host_context(value: Any) -> dict[str, Any]:
    field = "host_context"
    payload = mapping(value, field)
    keys = {
        "action_id",
        "run_ref",
        "producer_attempt_ref",
        "output_ref",
        "output_state",
    }
    for optional_field in (
        "build_dependency_currentness_authority_ref",
        "build_dependency_currentness_authority_issuer_attempt_ref",
    ):
        if optional_field in payload:
            keys.add(optional_field)
    exact_keys(
        payload,
        keys,
        field,
    )
    if payload.get("action_id") != "paper_mission":
        raise RequestShapeError("host_context.action_id must be paper_mission")
    authority_ref_present = "build_dependency_currentness_authority_ref" in payload
    issuer_ref_present = (
        "build_dependency_currentness_authority_issuer_attempt_ref" in payload
    )
    if authority_ref_present != issuer_ref_present:
        raise RequestShapeError(
            "host_context build dependency currentness authority refs must be "
            "supplied together"
        )
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
        "build_dependency_currentness_authority_ref": (
            _exact_ref(
                payload.get("build_dependency_currentness_authority_ref"),
                f"{field}.build_dependency_currentness_authority_ref",
                "mas_build_dependency_currentness_authority",
            )
            if authority_ref_present
            else None
        ),
        "build_dependency_currentness_authority_issuer_attempt_ref": (
            _typed_ref(
                payload.get(
                    "build_dependency_currentness_authority_issuer_attempt_ref"
                ),
                f"{field}.build_dependency_currentness_authority_issuer_attempt_ref",
                "opl_stage_attempt",
            )
            if issuer_ref_present
            else None
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
            "current_accepted_or_active_revision_intake_refs": None,
            "consumption_receipt_ref": None,
            "consumption_receipt": None,
        }
    payload = mapping(value, field)
    has_current_revision_inventory = (
        "current_accepted_or_active_revision_intake_refs" in payload
    )
    shape_payload = dict(payload)
    shape_payload.setdefault("current_accepted_or_active_revision_intake_refs", None)
    exact_keys(
        shape_payload,
        {
            "surface_kind",
            "schema_version",
            "current_accepted_or_active_revision_intake_refs",
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
    current_revision_intake_refs = None
    if has_current_revision_inventory:
        current_revision_intake_refs = _exact_ref_list(
            payload.get("current_accepted_or_active_revision_intake_refs"),
            f"{field}.current_accepted_or_active_revision_intake_refs",
            "opl_revision_intake",
        )
        current_revision_intake_refs.sort(key=_exact_ref_identity)
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
        "current_accepted_or_active_revision_intake_refs": (
            current_revision_intake_refs
        ),
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
