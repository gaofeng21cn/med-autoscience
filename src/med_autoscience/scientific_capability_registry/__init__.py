from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.scholarskills_required_package import (
    build_scholarskills_required_package_template,
)
from med_autoscience.scholarskills_capability_modules import (
    SCHOLAR_DISPLAY_EXECUTION_RECEIPT_EXPECTATION,
    SCHOLAR_DISPLAY_EXECUTION_RECEIPT_REF_ALIASES as _SCHOLAR_DISPLAY_EXECUTION_RECEIPT_REF_ALIASES,
    SCHOLAR_DISPLAY_MODULE_ID,
    SCHOLARSKILLS_CAPABILITY_IDS,
    scholarskills_execution_receipt_ref_aliases,
)
from .registry_contract import (
    OWNER_CONSUMPTION_EVIDENCE_SURFACE_KIND,
    STANDARD_AGENT_FALSE_COMPLETION_BLOCKERS as _STANDARD_AGENT_FALSE_COMPLETION_BLOCKERS,
    STANDARD_AGENT_FEEDBACK_LOOP_TAIL_KEYS as _STANDARD_AGENT_FEEDBACK_LOOP_TAIL_KEYS,
    authority_boundary as _authority_boundary,
    capability_inventory as _capability_inventory,
    capability_matches as _capability_matches,
    capability_request_projection as _capability_request_projection,
    current_owner_summary as _current_owner_summary,
    dedupe_texts as _dedupe_texts,
    descriptor_only_projection as _descriptor_only_projection,
    mapping as _mapping,
    merge_execution_receipt_input as _merge_execution_receipt_input,
    merge_mappings as _merge_mappings,
    no_forbidden_write_proof as _no_forbidden_write_proof_for_refs,
    opl_capability_invocation_request as _opl_capability_invocation_request,
    owner_response_refs as _owner_response_refs,
    resolution_candidate as _resolution_candidate,
    scholarskills_execution_receipt_evidence as _scholarskills_execution_receipt_evidence_for_capability,
    scholarskills_owner_gate_readback as _scholarskills_owner_gate_readback,
    standard_agent_feedback_loop_tail as _standard_agent_feedback_loop_tail,
    string_counts as _string_counts,
    text as _text,
    text_list as _text_list,
    text_set as _text_set,
    require_text as _require_text,
)
from med_autoscience.scholarskills_package_consumption import (
    build_scholarskills_materialized_package_input,
)
from med_autoscience.scientific_capability_registry_catalog import (
    _capabilities,
)


SURFACE_KIND = "mas_scientific_capability_registry"
SUMMARY_SURFACE_KIND = "mas_scientific_capability_registry_summary"
INVENTORY_SURFACE_KIND = "mas_scientific_capability_inventory"
RESOLUTION_SURFACE_KIND = "mas_scientific_capability_resolution"
INVOCATION_SURFACE_KIND = "mas_scientific_capability_invocation"
SCHEMA_VERSION = 1
DEFAULT_CURRENT_DELTA_TRIGGER = "current_delta_declares_or_implies_affordance_need"

def build_scientific_capability_registry() -> dict[str, Any]:
    capabilities = _capabilities()
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "owner": "MedAutoScience",
        "resolver_owner": "one-person-lab",
        "ordinary_planning_root": "current_owner_delta",
        "default_trigger": DEFAULT_CURRENT_DELTA_TRIGGER,
        "default_policy": {
            "fail_open": True,
            "fail_open_scope": "individual_refs_only_capability_after_required_package_is_current",
            "mainline_waits_for_capability": False,
            "missing_capability_blocks_owner_action": False,
            "required_capability_package_fail_closed": True,
            "external_runtime_dependency": False,
            "always_on_scan": False,
            "second_route_table": False,
            "wildcard_action_triggers_auto_select": False,
            "wildcard_action_triggers_require_explicit_capability_request": True,
        },
        "capability_count": len(capabilities),
        "capabilities": capabilities,
        "scholarskills_required_package": build_scholarskills_required_package_template(),
        "owner_consumption_evidence_schema": {
            "surface_kind": OWNER_CONSUMPTION_EVIDENCE_SURFACE_KIND,
            "schema_version": SCHEMA_VERSION,
            "counts_as_paper_truth": False,
            "counts_as_owner_receipt": False,
            "can_authorize_publication_readiness": False,
            "standard_agent_feedback_loop_tail": {
                "required_keys": list(_STANDARD_AGENT_FEEDBACK_LOOP_TAIL_KEYS),
                "false_completion_blockers": list(
                    _STANDARD_AGENT_FALSE_COMPLETION_BLOCKERS
                ),
                "mas_repo_can_close_opl_family_tail": False,
                "opl_hosted_runtime_consumption_required": True,
            },
            "scholar_display_execution_receipt": {
                "module_id": SCHOLAR_DISPLAY_MODULE_ID,
                "receipt_role": "candidate_display_execution_receipt",
                "required_ref_families": list(
                    SCHOLAR_DISPLAY_EXECUTION_RECEIPT_EXPECTATION[
                        "required_ref_families"
                    ]
                ),
                "accepted_ref_aliases": {
                    family: list(aliases)
                    for family, aliases in _SCHOLAR_DISPLAY_EXECUTION_RECEIPT_REF_ALIASES.items()
                },
                "status_values": [
                    "complete",
                    "missing_required_refs",
                ],
                "counts_as_paper_truth": False,
                "counts_as_owner_receipt": False,
                "can_authorize_publication_readiness": False,
            },
            "scholarskills_execution_receipts": {
                module_id: {
                    "module_id": module_id,
                    "receipt_role": "candidate_scholarskills_execution_receipt",
                    "required_ref_families": list(
                        _mapping(
                            _capability_by_id(module_id).get(
                                "execution_receipt_expectation"
                            )
                        ).get("required_ref_families")
                        or []
                    ),
                    "accepted_ref_aliases": {
                        family: list(aliases)
                        for family, aliases in scholarskills_execution_receipt_ref_aliases(
                            capability_id=module_id,
                            required_ref_families=_text_list(
                                _mapping(
                                    _capability_by_id(module_id).get(
                                        "execution_receipt_expectation"
                                    )
                                ).get("required_ref_families")
                            ),
                        ).items()
                    },
                    "status_values": [
                        "complete",
                        "missing_required_refs",
                    ],
                    "counts_as_paper_truth": False,
                    "counts_as_owner_receipt": False,
                    "can_authorize_publication_readiness": False,
                }
                for module_id in SCHOLARSKILLS_CAPABILITY_IDS
            },
        },
        "authority_boundary": _authority_boundary(),
    }


def build_scientific_capability_registry_summary() -> dict[str, Any]:
    capabilities = _capabilities()
    inventory = _capability_inventory(capabilities)
    return {
        "surface_kind": SUMMARY_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "registry_surface_kind": SURFACE_KIND,
        "capability_count": len(capabilities),
        "capability_family_count": len(
            {item["capability_family"] for item in capabilities}
        ),
        "module_capability_count": sum(1 for item in capabilities if item.get("module_id")),
        "descriptor_only_count": sum(1 for item in capabilities if item.get("descriptor_only")),
        "refs_only_count": sum(1 for item in capabilities if item.get("refs_only")),
        "wildcard_trigger_count": sum(
            1 for item in capabilities if item.get("wildcard_action_trigger_policy")
        ),
        "invocation_kind_counts": _string_counts(
            item["invocation_kind"] for item in capabilities
        ),
        "capability_families": sorted(
            {item["capability_family"] for item in capabilities}
        ),
        "capability_ids": [item["capability_id"] for item in inventory],
        "inventory_count": len(inventory),
        "authority_boundary": _authority_boundary(),
    }


def build_scientific_capability_registry_inventory() -> dict[str, Any]:
    capabilities = _capabilities()
    inventory = _capability_inventory(capabilities)
    return {
        "surface_kind": INVENTORY_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "registry_surface_kind": SURFACE_KIND,
        "inventory_count": len(inventory),
        "inventory": inventory,
        "capability_ids": [item["capability_id"] for item in inventory],
        "capability_families": sorted(
            {item["capability_family"] for item in capabilities}
        ),
        "authority_boundary": _authority_boundary(),
    }


def resolve_scientific_capabilities(
    *,
    current_owner_delta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    delta = _mapping(current_owner_delta)
    action_type = _text(delta.get("action_type")) or _text(delta.get("action_id")) or "unknown_action"
    requested_families = _text_set(delta.get("capability_families")) | _text_set(
        delta.get("route_required_ref_families")
    )
    candidates = [
        _resolution_candidate(capability, action_type=action_type, current_owner_delta=delta)
        for capability in _capabilities()
        if _capability_matches(
            capability,
            action_type=action_type,
            requested_families=requested_families,
            current_owner_delta=delta,
        )
    ]
    return {
        "surface_kind": RESOLUTION_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "resolved" if candidates else "no_matching_capability",
        "planning_root": "current_owner_delta",
        "current_owner_delta": _current_owner_summary(delta),
        "selected_capabilities": candidates,
        "selected_count": len(candidates),
        "fail_open": True,
        "mainline_waits_for_capability": False,
        "missing_capability_blocks_owner_action": False,
        "authority_boundary": _authority_boundary(),
    }


def invoke_scientific_capability(
    *,
    capability_id: str,
    current_owner_delta: Mapping[str, Any] | None = None,
    study_root: Path | str | None = None,
    apply: bool = False,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    capability = _capability_by_id(capability_id)
    delta = _mapping(current_owner_delta)
    runtime_request = _opl_capability_invocation_request(
        schema_version=SCHEMA_VERSION,
        capability=capability,
        current_owner_delta=delta,
        study_root=study_root,
        payload=payload,
    )
    invocation: dict[str, Any] = {
        "surface_kind": INVOCATION_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "capability_id": capability["capability_id"],
        "capability_family": capability["capability_family"],
        "status": "opl_capability_request_pending",
        "apply": bool(apply),
        "refs_only": True,
        "request_only": True,
        "mainline_waits_for_capability": False,
        "can_block_current_owner_action": False,
        "mas_local_capability_actuator": False,
        "mas_can_invoke_capability_sidecar": False,
        "opl_capability_runtime_required": True,
        "opl_capability_invocation_request": runtime_request,
        "output_refs": list(capability.get("output_refs") or []),
        "authority_boundary": _authority_boundary(),
        "result": _capability_request_projection(
            schema_version=SCHEMA_VERSION,
            capability=capability,
            current_owner_delta=delta,
            runtime_request=runtime_request,
        ),
    }
    if capability["invocation_kind"] == "descriptor_only_current_owner_input_refs":
        invocation.update(
            {
                "status": "descriptor_only",
                "request_only": False,
                "descriptor_only": True,
                "opl_capability_runtime_required": False,
                "external_runner_invocation_allowed": False,
                "result": _descriptor_only_projection(
                    schema_version=SCHEMA_VERSION,
                    capability=capability,
                    current_owner_delta=delta,
                    runtime_request=runtime_request,
                ),
            }
        )
    if capability["invocation_kind"] == "mas_domain_feedbackops_dispatch_request":
        invocation.update(
            {
                "status": "mas_domain_feedbackops_dispatch_available",
                "request_only": False,
                "descriptor_only": False,
                "mas_local_capability_actuator": True,
                "mas_can_invoke_capability_sidecar": True,
                "opl_capability_runtime_required": True,
                "external_runner_invocation_allowed": True,
            }
        )
    return invocation


def build_capability_owner_consumption_evidence(
    *,
    invocation_result: Mapping[str, Any],
    current_owner_delta: Mapping[str, Any] | None = None,
    owner_response_refs: Mapping[str, Any] | None = None,
    execution_receipt: Mapping[str, Any] | str | None = None,
    execution_receipt_path: Path | str | None = None,
    execution_receipt_refs: Mapping[str, Any] | None = None,
    materialized_package_manifest_path: Path | str | None = None,
    execution_receipt_ref: str | None = None,
    input_fingerprint_ref: str | None = None,
    dependency_profile_ref: str | None = None,
    dependency_prepared_receipt_ref: str | None = None,
    prepared_run_context_ref: str | None = None,
    run_context_ref: str | None = None,
    render_cache_ref: str | None = None,
    artifact_manifest_ref: str | None = None,
    visual_audit_or_gallery_preview_ref: str | None = None,
) -> dict[str, Any]:
    invocation = _mapping(invocation_result)
    owner_refs = _owner_response_refs(owner_response_refs)
    observed_owner_refs = [ref for ref in owner_refs.values() if ref is not None]
    evidence = {
        "surface_kind": OWNER_CONSUMPTION_EVIDENCE_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "recorded",
        "refs_only": True,
        "capability_id": _text(invocation.get("capability_id")),
        "capability_family": _text(invocation.get("capability_family")),
        "current_owner_delta_identity": _current_owner_summary(
            _mapping(current_owner_delta)
        ),
        "output_refs": _capability_output_refs(invocation),
        "owner_consumption_status": (
            "owner_response_refs_observed"
            if observed_owner_refs
            else "no_owner_response_refs"
        ),
        "owner_receipt_ref": owner_refs["owner_receipt_ref"],
        "typed_blocker_ref": owner_refs["typed_blocker_ref"],
        "reviewer_receipt_ref": owner_refs["reviewer_receipt_ref"],
        "route_back_evidence_ref": owner_refs["route_back_evidence_ref"],
        "counts_as_progress": False,
        "counts_as_paper_truth": False,
        "counts_as_owner_receipt": False,
        "consumption_evidence_only": True,
        "can_authorize_owner_action": False,
        "can_authorize_publication_readiness": False,
        "mainline_waits_for_owner_consumption": False,
        "fail_open": True,
        "missing_owner_response_refs_blocks": False,
        "standard_agent_feedback_loop_tail": _standard_agent_feedback_loop_tail(
            schema_version=SCHEMA_VERSION,
            owner_refs=owner_refs,
            observed_owner_refs=observed_owner_refs,
        ),
        "no_forbidden_write_proof": _no_forbidden_write_proof_for_refs(
            invocation=invocation,
            output_refs=_capability_output_refs(invocation),
        ),
        "fail_open_policy": {
            "missing_owner_response_refs_blocks": False,
            "missing_capability_output_blocks": False,
            "mainline_waits_for_live_soak": False,
            "external_runtime_dependency": False,
        },
        "authority_boundary": _authority_boundary(),
    }
    capability_id = _text(invocation.get("capability_id"))
    if capability_id in SCHOLARSKILLS_CAPABILITY_IDS:
        capability = _capability_by_id(capability_id)
        materialized_package = build_scholarskills_materialized_package_input(
            capability_id=capability_id,
            required_ref_families=_text_list(
                _mapping(
                    capability.get("execution_receipt_expectation")
                ).get("required_ref_families")
            ),
            execution_receipt_path=execution_receipt_path,
            materialized_package_manifest_path=materialized_package_manifest_path,
        )
        evidence.update(
            _scholarskills_execution_receipt_evidence_for_capability(
                capability_id=capability_id,
                capability=capability,
                execution_receipt=_merge_execution_receipt_input(
                    materialized_package.get("execution_receipt"),
                    execution_receipt,
                ),
                execution_receipt_refs=_merge_mappings(
                    materialized_package.get("execution_receipt_refs"),
                    execution_receipt_refs,
                ),
                explicit_refs={
                    "execution_receipt_ref": execution_receipt_ref,
                    "input_fingerprint_ref": input_fingerprint_ref,
                    "dependency_profile_ref": dependency_profile_ref,
                    "dependency_prepared_receipt_ref": dependency_prepared_receipt_ref,
                    "prepared_run_context_ref": prepared_run_context_ref,
                    "run_context_ref": run_context_ref,
                    "render_cache_ref": render_cache_ref,
                    "artifact_manifest_ref": artifact_manifest_ref,
                    "visual_audit_or_gallery_preview_ref": visual_audit_or_gallery_preview_ref,
                },
            )
        )
        if materialized_package:
            evidence["materialized_package_consumption"] = materialized_package[
                "materialized_package_consumption"
            ]
        owner_gate_readback = _scholarskills_owner_gate_readback(
            schema_version=SCHEMA_VERSION,
            evidence=evidence,
            current_owner_delta=_mapping(current_owner_delta),
        )
        if owner_gate_readback:
            evidence.update(owner_gate_readback)
    return evidence


def _capability_by_id(capability_id: str) -> dict[str, Any]:
    requested = _require_text(capability_id, "capability_id")
    for capability in _capabilities():
        if capability["capability_id"] == requested:
            return capability
    raise ValueError(f"Unknown scientific capability: {capability_id}")


def _capability_output_refs(invocation: Mapping[str, Any]) -> list[str]:
    result = _mapping(invocation.get("result"))
    refs: list[str] = []
    for key in ("allowed_writes", "written_refs", "output_refs"):
        refs.extend(_text_list(result.get(key)))
    refs.extend(_text_list(_mapping(invocation.get("opl_capability_invocation_request")).get("expected_output_refs")))
    refs.extend(_text_list(invocation.get("output_refs")))
    bundle_ref = _text(result.get("bundle_ref"))
    if bundle_ref:
        refs.append(bundle_ref)
    latest_ref = _text(result.get("latest_ref"))
    if latest_ref:
        refs.append(latest_ref)
    advisory_ref_paths = result.get("advisory_ref_paths")
    if isinstance(advisory_ref_paths, Mapping):
        refs.extend(_text_list(advisory_ref_paths.values()))
    if not refs:
        refs = _text_list(_capability_by_id(_text(invocation.get("capability_id"))).get("output_refs"))
    return _dedupe_texts(refs)


def _require_study_root(value: Path | str | None) -> Path:
    if value is None:
        raise ValueError("study_root is required to invoke this capability")
    return Path(value).expanduser().resolve()


def _path_or_none(value: Mapping[str, Any] | None, key: str) -> Path | None:
    if not isinstance(value, Mapping):
        return None
    text = _text(value.get(key))
    return Path(text).expanduser().resolve() if text else None


def _int_or_default(value: Mapping[str, Any] | None, key: str, default: int) -> int:
    if not isinstance(value, Mapping):
        return default
    raw = value.get(key)
    if isinstance(raw, int):
        return raw
    return default


__all__ = [
    "INVOCATION_SURFACE_KIND",
    "INVENTORY_SURFACE_KIND",
    "OWNER_CONSUMPTION_EVIDENCE_SURFACE_KIND",
    "RESOLUTION_SURFACE_KIND",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "build_scientific_capability_registry",
    "build_scientific_capability_registry_summary",
    "build_scientific_capability_registry_inventory",
    "build_capability_owner_consumption_evidence",
    "invoke_scientific_capability",
    "resolve_scientific_capabilities",
]
