from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.scholarskills_capability_modules import (
    SCHOLAR_DISPLAY_EXECUTION_RECEIPT_EXPECTATION,
    SCHOLAR_DISPLAY_EXECUTION_RECEIPT_REF_ALIASES,
    scholarskills_execution_receipt_ref_aliases,
)
from med_autoscience.scholarskills_package_consumption import (
    build_candidate_artifact_owner_request_items,
    build_scholarskills_materialized_package_input,
)


OWNER_CONSUMPTION_EVIDENCE_SURFACE_KIND = (
    "mas_scientific_capability_owner_consumption_evidence"
)
SCHOLARSKILLS_OWNER_GATE_REQUEST_SURFACE_KIND = "mas_scholarskills_owner_gate_request"
SCHOLARSKILLS_OWNER_GATE_HANDOFF_SURFACE_KIND = "mas_scholarskills_owner_gate_handoff"
OWNER_RESPONSE_REF_KEYS = (
    "owner_receipt_ref",
    "typed_blocker_ref",
    "reviewer_receipt_ref",
    "route_back_evidence_ref",
)
REQUIRED_OWNER_RESPONSE_SHAPES = (
    {
        "shape": "owner_receipt_ref",
        "required_for": "accept_candidate_into_mas_paper_truth",
        "may_be_written_by_this_request": False,
    },
    {
        "shape": "typed_blocker_ref",
        "required_for": "block_candidate_with_stable_owner_reason",
        "may_be_written_by_this_request": False,
    },
    {
        "shape": "route_back_evidence_ref",
        "required_for": "return_candidate_to_capability_or_executor",
        "may_be_written_by_this_request": False,
    },
    {
        "shape": "reviewer_receipt_ref",
        "required_for": "attach_non_authoritative_reviewer_readback",
        "may_be_written_by_this_request": False,
    },
)
FORBIDDEN_WRITE_CHECK_REFS = (
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    "paper",
    "package",
    "artifacts/publication_handoff/owner_receipt.json",
    "artifacts/publication_handoff/typed_blocker.json",
    "artifacts/medical_paper/readiness_owner_receipt.json",
    "artifacts/medical_paper/readiness_typed_blocker.json",
)
FORBIDDEN_PATH_ABSENCE_REFS = (
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    "paper",
    "package",
)
STANDARD_AGENT_FEEDBACK_LOOP_TAIL_KEYS = (
    "production_generated_surface_caller_negative_samples_ref",
    "real_target_owner_accepted_answer_or_typed_blocker_scaleout_ref",
    "long_soak_negative_conformance_ref",
)
STANDARD_AGENT_FALSE_COMPLETION_BLOCKERS = (
    "MAS_contract_landed_without_OPL_family_consumption",
    "suite_pass_without_target_owner_receipt_or_typed_blocker",
    "hosted_consumption_packet_without_live_owner_answer",
    "domain_local_selector_or_always_on_sidecar",
)
CURRENT_DELTA_DECLARATION_KEYS = {
    "action_type",
    "action_id",
    "artifact_kind",
    "artifact_need",
    "capability_id",
    "capability_ids",
    "capability_families",
    "capability_family",
    "declared_need",
    "declared_needs",
    "display_need",
    "figure_need",
    "intent",
    "manifest_need",
    "need",
    "paper_need",
    "output_kind",
    "requested_refs",
    "requested_surface",
    "route_required_ref_families",
    "route_required_ref_family",
    "router_need",
    "stable_plotting_need",
    "target_surface",
}


def owner_response_refs(value: Mapping[str, Any] | None) -> dict[str, str | None]:
    refs = mapping(value)
    return {key: (text(refs.get(key)) or None) for key in OWNER_RESPONSE_REF_KEYS}


def standard_agent_feedback_loop_tail(
    *,
    schema_version: int,
    owner_refs: Mapping[str, str | None],
    observed_owner_refs: list[str],
) -> dict[str, Any]:
    owner_answer_refs = [
        ref
        for key, ref in owner_refs.items()
        if key in {"owner_receipt_ref", "typed_blocker_ref"} and ref is not None
    ]
    return {
        "surface_kind": "mas_standard_agent_feedback_loop_tail_evidence",
        "schema_version": schema_version,
        "required_tail_keys": list(STANDARD_AGENT_FEEDBACK_LOOP_TAIL_KEYS),
        "repo_side_shape_landed": True,
        "production_generated_surface_caller_negative_samples_ref": None,
        "real_target_owner_accepted_answer_or_typed_blocker_scaleout_ref": (
            owner_answer_refs[0] if owner_answer_refs else None
        ),
        "observed_owner_response_refs": list(observed_owner_refs),
        "owner_answer_or_typed_blocker_observed": bool(owner_answer_refs),
        "long_soak_negative_conformance_ref": None,
        "missing_external_tail_keys": [
            key
            for key in STANDARD_AGENT_FEEDBACK_LOOP_TAIL_KEYS
            if key != "real_target_owner_accepted_answer_or_typed_blocker_scaleout_ref"
            or not owner_answer_refs
        ],
        "false_completion_blockers": list(STANDARD_AGENT_FALSE_COMPLETION_BLOCKERS),
        "mas_repo_can_close_opl_family_tail": False,
        "opl_hosted_runtime_consumption_required": True,
        "counts_as_opl_family_completion": False,
    }


def scholar_display_execution_receipt_evidence(
    *,
    execution_receipt: Mapping[str, Any] | str | None,
    execution_receipt_refs: Mapping[str, Any] | None,
    explicit_refs: Mapping[str, Any],
) -> dict[str, Any]:
    refs = scholar_display_execution_receipt_refs(
        execution_receipt=execution_receipt,
        execution_receipt_refs=execution_receipt_refs,
        explicit_refs=explicit_refs,
    )
    required = text_list(
        SCHOLAR_DISPLAY_EXECUTION_RECEIPT_EXPECTATION.get("required_ref_families")
    )
    observed = [family for family in required if text(refs.get(family))]
    missing = [family for family in required if family not in observed]
    execution_receipt_ref = text(refs.get("execution_receipt_ref")) or None
    status = "complete" if not missing else "missing_required_refs"
    return {
        "execution_receipt_ref": execution_receipt_ref,
        "execution_receipt_refs": {
            family: text(refs.get(family))
            for family in required
            if text(refs.get(family))
        },
        "execution_receipt_status": status,
        "missing_execution_receipt_ref_families": missing,
        "observed_execution_receipt_ref_families": observed,
        "execution_receipt_expectation": dict(
            SCHOLAR_DISPLAY_EXECUTION_RECEIPT_EXPECTATION
        ),
        "execution_receipt_counts_as_candidate_artifact": status == "complete",
        "counts_as_paper_truth": False,
        "counts_as_owner_receipt": False,
        "can_authorize_publication_readiness": False,
    }


def scholarskills_execution_receipt_evidence(
    *,
    capability_id: str,
    capability: Mapping[str, Any],
    execution_receipt: Mapping[str, Any] | str | None,
    execution_receipt_refs: Mapping[str, Any] | None,
    explicit_refs: Mapping[str, Any],
) -> dict[str, Any]:
    expectation = mapping(capability.get("execution_receipt_expectation"))
    required = text_list(expectation.get("required_ref_families"))
    refs = scholarskills_execution_receipt_refs(
        capability_id=capability_id,
        required_ref_families=required,
        execution_receipt=execution_receipt,
        execution_receipt_refs=execution_receipt_refs,
        explicit_refs=explicit_refs,
    )
    observed = [family for family in required if text(refs.get(family))]
    missing = [family for family in required if family not in observed]
    execution_receipt_ref = text(refs.get("execution_receipt_ref")) or None
    status = "complete" if not missing else "missing_required_refs"
    return {
        "execution_receipt_ref": execution_receipt_ref,
        "execution_receipt_refs": {
            family: text(refs.get(family))
            for family in required
            if text(refs.get(family))
        },
        "execution_receipt_status": status,
        "missing_execution_receipt_ref_families": missing,
        "observed_execution_receipt_ref_families": observed,
        "execution_receipt_expectation": dict(expectation),
        "execution_receipt_counts_as_candidate_artifact": status == "complete",
        "counts_as_paper_truth": False,
        "counts_as_owner_receipt": False,
        "can_authorize_publication_readiness": False,
    }


def scholarskills_execution_receipt_refs(
    *,
    capability_id: str,
    required_ref_families: list[str],
    execution_receipt: Mapping[str, Any] | str | None,
    execution_receipt_refs: Mapping[str, Any] | None,
    explicit_refs: Mapping[str, Any],
) -> dict[str, str]:
    raw: dict[str, Any] = {}
    if isinstance(execution_receipt, str):
        raw["execution_receipt_ref"] = execution_receipt
    else:
        raw.update(mapping(execution_receipt))
    raw.update(mapping(execution_receipt_refs))
    raw.update({key: value for key, value in explicit_refs.items() if text(value)})

    nested_refs = mapping(raw.get("refs"))
    if nested_refs:
        raw.update({key: value for key, value in nested_refs.items() if key not in raw})
    nested_execution_refs = mapping(raw.get("execution_receipt_refs"))
    if nested_execution_refs:
        raw.update(
            {key: value for key, value in nested_execution_refs.items() if key not in raw}
        )

    result: dict[str, str] = {}
    execution_receipt_ref = (
        text(raw.get("execution_receipt_ref"))
        or text(raw.get("receipt_ref"))
        or text(raw.get("receipt_uri"))
    )
    if execution_receipt_ref:
        result["execution_receipt_ref"] = execution_receipt_ref
    aliases_by_family = scholarskills_execution_receipt_ref_aliases(
        capability_id=capability_id,
        required_ref_families=required_ref_families,
    )
    for family, aliases in aliases_by_family.items():
        for alias in aliases:
            ref = text(raw.get(alias))
            if ref:
                result[family] = ref
                break
    return result


def scholarskills_owner_gate_readback(
    *,
    schema_version: int,
    evidence: Mapping[str, Any],
    current_owner_delta: Mapping[str, Any],
) -> dict[str, Any]:
    package = mapping(evidence.get("materialized_package_consumption"))
    if not scholarskills_owner_gate_requestable(evidence=evidence, package=package):
        return {}
    request = scholarskills_owner_gate_request(
        schema_version=schema_version,
        evidence=evidence,
        package=package,
        current_owner_delta=current_owner_delta,
    )
    return {
        "owner_gate_request": request,
        "owner_gate_handoff": scholarskills_owner_gate_handoff(
            schema_version=schema_version,
            request=request,
            package=package,
        ),
        "required_owner_response_shapes": [
            dict(shape) for shape in REQUIRED_OWNER_RESPONSE_SHAPES
        ],
    }


def scholarskills_owner_gate_requestable(
    *,
    evidence: Mapping[str, Any],
    package: Mapping[str, Any],
) -> bool:
    return (
        bool(package)
        and text(evidence.get("execution_receipt_status")) == "complete"
        and package.get("authority_flags_false") is True
        and not text_list(package.get("forbidden_written_file_collisions"))
        and not text_list(package.get("mas_consumer_written_files"))
    )


def scholarskills_owner_gate_request(
    *,
    schema_version: int,
    evidence: Mapping[str, Any],
    package: Mapping[str, Any],
    current_owner_delta: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_artifacts = build_candidate_artifact_owner_request_items(package)
    return {
        "surface_kind": SCHOLARSKILLS_OWNER_GATE_REQUEST_SURFACE_KIND,
        "schema_version": schema_version,
        "request_status": "ready_for_owner_gate_review",
        "request_role": "non_authoritative_scholarskills_candidate_review_request",
        "non_authoritative_request": True,
        "refs_only": True,
        "capability_id": text(evidence.get("capability_id")),
        "capability_family": text(evidence.get("capability_family")),
        "module_id": text(package.get("module_id")) or text(evidence.get("capability_id")),
        "current_owner_delta_identity": current_owner_summary(current_owner_delta),
        "execution_receipt_ref": text(evidence.get("execution_receipt_ref")) or None,
        "execution_receipt_status": text(evidence.get("execution_receipt_status")),
        "execution_receipt_refs": dict(mapping(evidence.get("execution_receipt_refs"))),
        "observed_execution_receipt_ref_families": text_list(
            evidence.get("observed_execution_receipt_ref_families")
        ),
        "materialized_package_manifest_path": text(package.get("manifest_path")) or None,
        "materialized_package_execution_receipt_path": text(
            package.get("execution_receipt_path")
        )
        or None,
        "materialized_package_sha256": text(package.get("sha256")) or None,
        "materialized_package_written_files": text_list(package.get("written_files")),
        "candidate_artifacts": candidate_artifacts,
        "candidate_artifact_count": len(candidate_artifacts),
        "candidate_artifact_missing_inputs": text_list(
            package.get("candidate_artifact_missing_inputs")
        ),
        "required_owner_response_shapes": [
            text(shape["shape"]) for shape in REQUIRED_OWNER_RESPONSE_SHAPES
        ],
        "counts_as_progress": False,
        "counts_as_paper_truth": False,
        "counts_as_owner_receipt": False,
        "counts_as_current_package_authority": False,
        "can_authorize_owner_action": False,
        "can_authorize_publication_readiness": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_write_human_gate": False,
        "authority_boundary": authority_boundary(),
    }


def scholarskills_owner_gate_handoff(
    *,
    schema_version: int,
    request: Mapping[str, Any],
    package: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface_kind": SCHOLARSKILLS_OWNER_GATE_HANDOFF_SURFACE_KIND,
        "schema_version": schema_version,
        "handoff_status": "ready_for_owner_gate_review",
        "handoff_role": "mas_owner_gate_review_handoff",
        "source_request_ref": "inline:owner_gate_request",
        "next_owner": "MAS owner gate",
        "capability_id": text(request.get("capability_id")),
        "module_id": text(request.get("module_id")),
        "candidate_artifacts": build_candidate_artifact_owner_request_items(request),
        "candidate_artifact_missing_inputs": text_list(
            request.get("candidate_artifact_missing_inputs")
        ),
        "required_owner_response_shapes": [
            dict(shape) for shape in REQUIRED_OWNER_RESPONSE_SHAPES
        ],
        "forbidden_authority_writes_absent": (
            package.get("authority_flags_false") is True
            and not text_list(package.get("forbidden_written_file_collisions"))
        ),
        "mas_consumer_written_files": [],
        "counts_as_progress": False,
        "counts_as_paper_truth": False,
        "counts_as_owner_receipt": False,
    }


def scholar_display_execution_receipt_refs(
    *,
    execution_receipt: Mapping[str, Any] | str | None,
    execution_receipt_refs: Mapping[str, Any] | None,
    explicit_refs: Mapping[str, Any],
) -> dict[str, str]:
    raw = _merged_execution_ref_input(
        execution_receipt=execution_receipt,
        execution_receipt_refs=execution_receipt_refs,
        explicit_refs=explicit_refs,
    )
    result: dict[str, str] = {}
    execution_receipt_ref = (
        text(raw.get("execution_receipt_ref"))
        or text(raw.get("receipt_ref"))
        or text(raw.get("receipt_uri"))
    )
    if execution_receipt_ref:
        result["execution_receipt_ref"] = execution_receipt_ref
    for family, aliases in SCHOLAR_DISPLAY_EXECUTION_RECEIPT_REF_ALIASES.items():
        for alias in aliases:
            ref = text(raw.get(alias))
            if ref:
                result[family] = ref
                break
    return result


def no_forbidden_write_proof(
    *,
    invocation: Mapping[str, Any],
    output_refs: list[str],
) -> dict[str, Any]:
    result = mapping(invocation.get("result"))
    study_root_text = text(result.get("study_root_ref")) or text(result.get("study_root"))
    existing_forbidden_refs: list[str] = []
    if study_root_text:
        study_root = Path(study_root_text).expanduser()
        for ref in FORBIDDEN_PATH_ABSENCE_REFS:
            if (study_root / ref).exists():
                existing_forbidden_refs.append(ref)
    output_ref_set = set(output_refs)
    forbidden_ref_collisions = [
        ref for ref in FORBIDDEN_WRITE_CHECK_REFS if ref in output_ref_set
    ]
    return {
        "checked_relative_refs": list(FORBIDDEN_WRITE_CHECK_REFS),
        "study_root_ref": study_root_text or None,
        "existing_forbidden_refs": existing_forbidden_refs,
        "forbidden_ref_collisions": forbidden_ref_collisions,
        "forbidden_refs_absent": (
            not existing_forbidden_refs and not forbidden_ref_collisions
        ),
        "proof_scope": (
            "path_absence_and_output_ref_collision"
            if study_root_text
            else "output_ref_collision_only"
        ),
    }


def capability_inventory(capabilities: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "capability_id": text(capability.get("capability_id")),
            "capability_family": text(capability.get("capability_family")),
            "module_id": text(capability.get("module_id")) or None,
            "invocation_kind": text(capability.get("invocation_kind")),
            "refs_only": bool(capability.get("refs_only")),
            "descriptor_only": bool(capability.get("descriptor_only")),
            "external_runner_invocation_allowed": bool(
                capability.get("external_runner_invocation_allowed", False)
            ),
            "source_frameworks": text_list(capability.get("source_frameworks")),
            "action_triggers": text_list(capability.get("action_triggers")),
            "output_refs": text_list(capability.get("output_refs")),
            "role": text(capability.get("role")),
        }
        for capability in capabilities
    ]


def resolution_candidate(
    capability: Mapping[str, Any],
    *,
    action_type: str,
    current_owner_delta: Mapping[str, Any],
) -> dict[str, Any]:
    candidate = {
        "capability_id": capability["capability_id"],
        "capability_family": capability["capability_family"],
        "source_frameworks": list(capability.get("source_frameworks") or []),
        "candidate_ref": f"scientific-capability:{capability['capability_id']}:{action_type}",
        "invocation_kind": capability["invocation_kind"],
        "callable_surface": capability["callable_surface"],
        "output_refs": list(capability.get("output_refs") or []),
        "artifact_refs": list(capability.get("artifact_refs") or []),
        "role": capability["role"],
        "trigger_reason": trigger_reason(
            capability,
            action_type=action_type,
            current_owner_delta=current_owner_delta,
        ),
        "refs_only": True,
        "body_included": False,
        "can_block_current_owner_action": False,
        "requires_explicit_invoke": True,
        "descriptor_only": bool(capability.get("descriptor_only")),
        "external_runner_invocation_allowed": bool(
            capability.get("external_runner_invocation_allowed", False)
        ),
        "contract_refs": list(capability.get("contract_refs") or []),
        "descriptor_refs": list(capability.get("descriptor_refs") or []),
        "dependency_profile_refs": list(capability.get("dependency_profile_refs") or []),
        "run_context_refs": list(capability.get("run_context_refs") or []),
        "execution_receipt_expectation": dict(
            mapping(capability.get("execution_receipt_expectation"))
        ),
        "owner_consumption_boundary": dict(
            mapping(capability.get("owner_consumption_boundary"))
        ),
        "bridged_capability_refs": list(capability.get("bridged_capability_refs") or []),
        "readback": capability_readback(capability),
        "authority_boundary": authority_boundary(),
    }
    module_id = text(capability.get("module_id"))
    if module_id:
        candidate["module_id"] = module_id
    wildcard_policy = mapping(capability.get("wildcard_action_trigger_policy"))
    if wildcard_policy:
        candidate["wildcard_action_trigger_policy"] = dict(wildcard_policy)
    return candidate


def capability_matches(
    capability: Mapping[str, Any],
    *,
    action_type: str,
    requested_families: set[str],
    current_owner_delta: Mapping[str, Any],
) -> bool:
    family = text(capability.get("capability_family"))
    if family in requested_families or text(capability.get("capability_id")) in requested_families:
        return True
    triggers = set(text_list(capability.get("action_triggers")))
    if action_type in triggers:
        return True
    return current_delta_declares_terms(
        current_owner_delta,
        terms=text_list(capability.get("current_delta_trigger_terms")),
    )


def trigger_reason(
    capability: Mapping[str, Any],
    *,
    action_type: str,
    current_owner_delta: Mapping[str, Any],
) -> str:
    requested = text_set(current_owner_delta.get("capability_families")) | text_set(
        current_owner_delta.get("route_required_ref_families")
    )
    if text(capability.get("capability_family")) in requested:
        return "current_delta_requested_capability_family"
    if text(capability.get("capability_id")) in requested:
        return "current_delta_requested_capability_id"
    if action_type in set(text_list(capability.get("action_triggers"))):
        return "action_type_trigger"
    if current_delta_declares_terms(
        current_owner_delta,
        terms=text_list(capability.get("current_delta_trigger_terms")),
    ):
        return (
            text(capability.get("current_delta_trigger_reason"))
            or "current_delta_declared_capability_need"
        )
    return "default_jit_affordance"


def capability_readback(capability: Mapping[str, Any]) -> dict[str, Any]:
    descriptor_only = (
        capability["invocation_kind"] == "descriptor_only_current_owner_input_refs"
    )
    readback = {
        "surface_kind": "mas_scientific_capability_readback",
        "capability_id": capability["capability_id"],
        "invocation_kind": capability["invocation_kind"],
        "descriptor_only": descriptor_only,
        "refs_only": True,
        "request_only": not descriptor_only,
        "can_execute_external_runner": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_quality_verdict": False,
        "contract_refs": list(capability.get("contract_refs") or []),
    }
    module_id = text(capability.get("module_id"))
    if module_id:
        readback["module_id"] = module_id
    for key in (
        "descriptor_refs",
        "dependency_profile_refs",
        "run_context_refs",
        "artifact_refs",
    ):
        refs = list(capability.get(key) or [])
        if refs:
            readback[key] = refs
    execution_receipt_expectation = mapping(
        capability.get("execution_receipt_expectation")
    )
    if execution_receipt_expectation:
        readback["execution_receipt_expectation"] = dict(execution_receipt_expectation)
    owner_consumption_boundary = mapping(capability.get("owner_consumption_boundary"))
    if owner_consumption_boundary:
        readback["owner_consumption_boundary"] = dict(owner_consumption_boundary)
    if module_id:
        readback["authority_false_flags"] = authority_false_flags()
    return readback


def opl_capability_invocation_request(
    *,
    schema_version: int,
    capability: Mapping[str, Any],
    current_owner_delta: Mapping[str, Any],
    study_root: Path | str | None,
    payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    delta = mapping(current_owner_delta)
    request_payload = mapping(payload)
    study_root_ref = text(study_root)
    return {
        "surface_kind": "mas_opl_capability_invocation_request",
        "schema_version": schema_version,
        "target_runtime_owner": "one-person-lab",
        "target_runtime_kind": "CapabilityRegistry",
        "request_owner": "med-autoscience",
        "authority_role": "capability_request_only",
        "capability_id": capability["capability_id"],
        "capability_family": capability["capability_family"],
        "invocation_kind": capability["invocation_kind"],
        "callable_surface": capability["callable_surface"],
        "study_root_ref": study_root_ref or None,
        "current_owner_delta_identity": current_owner_summary(delta),
        "expected_output_refs": list(capability.get("output_refs") or []),
        "payload_ref": text(request_payload.get("payload_ref")) or None,
        "mas_can_create_opl_outbox_record": False,
        "mas_can_create_opl_event": False,
        "mas_can_create_opl_stage_run": False,
        "mas_can_run_capability_actuator": False,
        "mainline_waits_for_capability": False,
    }


def capability_request_projection(
    *,
    schema_version: int,
    capability: Mapping[str, Any],
    current_owner_delta: Mapping[str, Any],
    runtime_request: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_scientific_capability_invocation_request_projection",
        "schema_version": schema_version,
        "status": "opl_capability_request_pending",
        "capability_ref": capability["capability_ref"],
        "capability_id": capability["capability_id"],
        "capability_family": capability["capability_family"],
        "invocation_kind": capability["invocation_kind"],
        "refs_only": True,
        "body_included": False,
        "current_owner_delta_identity": current_owner_summary(current_owner_delta),
        "output_refs": list(capability.get("output_refs") or []),
        "opl_capability_invocation_request": dict(runtime_request),
        "mas_local_capability_actuator": False,
        "mainline_waits_for_capability": False,
        "can_block_current_owner_action": False,
        "authority_boundary": authority_boundary(),
    }


def descriptor_only_projection(
    *,
    schema_version: int,
    capability: Mapping[str, Any],
    current_owner_delta: Mapping[str, Any],
    runtime_request: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_scientific_capability_descriptor_only_projection",
        "schema_version": schema_version,
        "status": "descriptor_only",
        "capability_ref": capability["capability_ref"],
        "capability_id": capability["capability_id"],
        "capability_family": capability["capability_family"],
        "invocation_kind": capability["invocation_kind"],
        "refs_only": True,
        "descriptor_only": True,
        "request_only": False,
        "body_included": False,
        "current_owner_delta_identity": current_owner_summary(current_owner_delta),
        "output_refs": list(capability.get("output_refs") or []),
        "contract_refs": list(capability.get("contract_refs") or []),
        "readback": capability_readback(capability),
        "opl_capability_invocation_request": dict(runtime_request),
        "mas_local_capability_actuator": False,
        "external_runner_invocation_allowed": False,
        "mainline_waits_for_capability": False,
        "can_block_current_owner_action": False,
        "authority_boundary": authority_boundary(),
    }


def current_delta_declares_terms(
    current_owner_delta: Mapping[str, Any],
    *,
    terms: list[str],
) -> bool:
    if not terms:
        return False
    haystack = " ".join(current_delta_declaration_texts(current_owner_delta)).lower()
    return any(term.lower() in haystack for term in terms)


def current_delta_declaration_texts(value: object) -> list[str]:
    if isinstance(value, Mapping):
        texts: list[str] = []
        for key, item in value.items():
            if key in CURRENT_DELTA_DECLARATION_KEYS or str(key).endswith(
                ("_ref", "_refs", "_need", "_needs", "_kind", "_surface")
            ):
                texts.append(str(key))
                texts.extend(current_delta_declaration_texts(item))
            elif isinstance(item, Mapping):
                texts.extend(current_delta_declaration_texts(item))
        return texts
    if isinstance(value, (list, tuple, set)):
        texts = []
        for item in value:
            texts.extend(current_delta_declaration_texts(item))
        return texts
    result = text(value)
    return [result] if result else []


def current_owner_summary(delta: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "action_type": text(delta.get("action_type")),
        "action_id": text(delta.get("action_id")),
        "owner": text(delta.get("owner")),
        "work_unit_id": text(delta.get("work_unit_id")),
        "work_unit_fingerprint": text(delta.get("work_unit_fingerprint")),
        "source_ref": text(delta.get("source_ref")),
    }


def authority_boundary() -> dict[str, bool | str]:
    return {
        "surface_role": "current_delta_bound_capability_resolver",
        "can_write_domain_truth": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_write_paper_or_package": False,
        "can_write_memory_body": False,
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_authorize_owner_action": False,
        "can_authorize_provider_attempt": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_artifact_authority": False,
        "capability_or_sidecar_can_be_admission_gate": False,
        "missing_capability_blocks_owner_action": False,
        "failed_capability_blocks_owner_action": False,
        "low_confidence_capability_blocks_owner_action": False,
        "sidecar_completion_required_for_stage_closeout": False,
        "can_close_stage": False,
    }


def authority_false_flags() -> dict[str, bool]:
    authority = authority_boundary()
    return {
        key: value
        for key, value in authority.items()
        if key.startswith("can_") and value is False
    }


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def merge_mappings(*values: object) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for value in values:
        result.update(mapping(value))
    return result


def merge_execution_receipt_input(*values: object) -> Mapping[str, Any] | str | None:
    result: dict[str, Any] = {}
    string_ref: str | None = None
    for value in values:
        if isinstance(value, str):
            string_ref = value
            continue
        result.update(mapping(value))
    return result or string_ref


def text(value: object) -> str:
    return str(value or "").strip()


def require_text(value: object, label: str) -> str:
    result = text(value)
    if not result:
        raise ValueError(f"{label} is required")
    return result


def text_list(value: object) -> list[str]:
    if isinstance(value, (str, Path)):
        result = text(value)
        return [result] if result else []
    if not isinstance(value, (list, tuple, set)):
        return []
    return [result for item in value if (result := text(item))]


def text_set(value: object) -> set[str]:
    return set(text_list(value))


def dedupe_texts(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def string_counts(values: list[str] | tuple[str, ...] | Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        result = text(value)
        if not result:
            continue
        counts[result] = counts.get(result, 0) + 1
    return dict(sorted(counts.items()))


def _merged_execution_ref_input(
    *,
    execution_receipt: Mapping[str, Any] | str | None,
    execution_receipt_refs: Mapping[str, Any] | None,
    explicit_refs: Mapping[str, Any],
) -> dict[str, Any]:
    raw: dict[str, Any] = {}
    if isinstance(execution_receipt, str):
        raw["execution_receipt_ref"] = execution_receipt
    else:
        raw.update(mapping(execution_receipt))
    raw.update(mapping(execution_receipt_refs))
    raw.update({key: value for key, value in explicit_refs.items() if text(value)})

    nested_refs = mapping(raw.get("refs"))
    if nested_refs:
        raw.update({key: value for key, value in nested_refs.items() if key not in raw})
    nested_execution_refs = mapping(raw.get("execution_receipt_refs"))
    if nested_execution_refs:
        raw.update(
            {key: value for key, value in nested_execution_refs.items() if key not in raw}
        )
    return raw
