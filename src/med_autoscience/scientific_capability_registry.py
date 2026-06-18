from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience import external_learning_adoption_closure
from med_autoscience.runtime_protocol import evo_scientist_sidecar_refs


SURFACE_KIND = "mas_scientific_capability_registry"
RESOLUTION_SURFACE_KIND = "mas_scientific_capability_resolution"
INVOCATION_SURFACE_KIND = "mas_scientific_capability_invocation"
OWNER_CONSUMPTION_EVIDENCE_SURFACE_KIND = (
    "mas_scientific_capability_owner_consumption_evidence"
)
SCHEMA_VERSION = 1
DEFAULT_CURRENT_DELTA_TRIGGER = "current_delta_declares_or_implies_affordance_need"
_OWNER_RESPONSE_REF_KEYS = (
    "owner_receipt_ref",
    "typed_blocker_ref",
    "reviewer_receipt_ref",
    "route_back_evidence_ref",
)
_FORBIDDEN_WRITE_CHECK_REFS = (
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    "paper",
    "package",
    "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json",
    "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
)
_FORBIDDEN_PATH_ABSENCE_REFS = (
    "artifacts/publication_eval/latest.json",
    "artifacts/controller_decisions/latest.json",
    "paper",
    "package",
)
_STANDARD_AGENT_FEEDBACK_LOOP_TAIL_KEYS = (
    "production_generated_surface_caller_negative_samples_ref",
    "real_target_owner_accepted_answer_or_typed_blocker_scaleout_ref",
    "long_soak_negative_conformance_ref",
)
_STANDARD_AGENT_FALSE_COMPLETION_BLOCKERS = (
    "MAS_contract_landed_without_OPL_family_consumption",
    "suite_pass_without_target_owner_receipt_or_typed_blocker",
    "hosted_consumption_packet_without_live_owner_answer",
    "domain_local_selector_or_always_on_sidecar",
)


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
            "mainline_waits_for_capability": False,
            "missing_capability_blocks_owner_action": False,
            "external_runtime_dependency": False,
            "always_on_scan": False,
            "second_route_table": False,
        },
        "capability_count": len(capabilities),
        "capabilities": capabilities,
        "owner_consumption_evidence_schema": {
            "surface_kind": OWNER_CONSUMPTION_EVIDENCE_SURFACE_KIND,
            "schema_version": SCHEMA_VERSION,
            "standard_agent_feedback_loop_tail": {
                "required_keys": list(_STANDARD_AGENT_FEEDBACK_LOOP_TAIL_KEYS),
                "false_completion_blockers": list(
                    _STANDARD_AGENT_FALSE_COMPLETION_BLOCKERS
                ),
                "mas_repo_can_close_opl_family_tail": False,
                "opl_hosted_runtime_consumption_required": True,
            },
        },
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
            capability=capability,
            current_owner_delta=delta,
            runtime_request=runtime_request,
        ),
    }
    if capability["invocation_kind"] == "descriptor_only_current_owner_input_refs":
        invocation["status"] = "descriptor_only"
        invocation["result"] = {
            "capability_ref": capability["capability_ref"],
            "next_step": capability["invocation_kind"],
            "opl_capability_invocation_request": runtime_request,
            "mas_local_capability_actuator": False,
        }
    return invocation


def build_capability_owner_consumption_evidence(
    *,
    invocation_result: Mapping[str, Any],
    current_owner_delta: Mapping[str, Any] | None = None,
    owner_response_refs: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    invocation = _mapping(invocation_result)
    owner_refs = _owner_response_refs(owner_response_refs)
    observed_owner_refs = [ref for ref in owner_refs.values() if ref is not None]
    return {
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
        "consumption_evidence_only": True,
        "can_authorize_owner_action": False,
        "mainline_waits_for_owner_consumption": False,
        "fail_open": True,
        "missing_owner_response_refs_blocks": False,
        "standard_agent_feedback_loop_tail": _standard_agent_feedback_loop_tail(
            owner_refs=owner_refs,
            observed_owner_refs=observed_owner_refs,
        ),
        "no_forbidden_write_proof": _no_forbidden_write_proof(invocation),
        "fail_open_policy": {
            "missing_owner_response_refs_blocks": False,
            "missing_capability_output_blocks": False,
            "mainline_waits_for_live_soak": False,
            "external_runtime_dependency": False,
        },
        "authority_boundary": _authority_boundary(),
    }


def _capabilities() -> list[dict[str, Any]]:
    return [
        _capability(
            capability_id="external_learning_authoring_advisory",
            capability_family="external_learning_sidecar",
            source_frameworks=["PaperSpine", "PaperOrchestra", "Academic Research Skills"],
            action_triggers=["run_quality_repair_batch"],
            invocation_kind="external_learning_sidecar",
            callable_surface=external_learning_adoption_closure.SIDECAR_CALLABLE_SURFACE,
            output_refs=[external_learning_adoption_closure.SIDECAR_RESULT_RELATIVE_PATH.as_posix()],
            role="authoring_and_claim_support_refs_only_advisory",
        ),
        _capability(
            capability_id="external_learning_review_and_progress_advisory",
            capability_family="external_learning_sidecar",
            source_frameworks=["ARIS", "ARK", "AutoSci / OmegaWiki"],
            action_triggers=[
                "unit_harmonized_external_validation_rerun",
                "run_gate_clearing_batch",
                "return_to_ai_reviewer_workflow",
            ],
            invocation_kind="external_learning_sidecar",
            callable_surface=external_learning_adoption_closure.SIDECAR_CALLABLE_SURFACE,
            output_refs=[external_learning_adoption_closure.SIDECAR_RESULT_RELATIVE_PATH.as_posix()],
            role="review_import_source_experiment_and_progress_refs_only_advisory",
        ),
        _capability(
            capability_id="evo_scientist_progress_sidecar",
            capability_family="progress_accelerator",
            source_frameworks=["EvoScientist", "EvoSkills"],
            action_triggers=["*"],
            invocation_kind="evo_scientist_sidecar",
            callable_surface=evo_scientist_sidecar_refs.WRITER_REF,
            output_refs=[str(evo_scientist_sidecar_refs.LATEST_REF)],
            role="background_memory_tool_affordance_failed_path_stop_loss_refs",
        ),
        _capability(
            capability_id="light_external_skill_content_advisory",
            capability_family="light_advisory",
            source_frameworks=["Light"],
            action_triggers=["*"],
            invocation_kind="light_advisory_materializer",
            callable_surface=(
                "med_autoscience.controllers.light_advisory_materializer."
                "materialize_light_advisory_refs"
            ),
            output_refs=["artifacts/stage_outputs/<stage>/advisory/light_external_pattern_refs.json"],
            role="verified_asset_collision_fresh_evidence_and_skill_content_refs",
        ),
        _capability(
            capability_id="co_scientist_current_owner_affordance",
            capability_family="hypothesis_review_affordance",
            source_frameworks=["Co-Scientist"],
            action_triggers=[
                "return_to_ai_reviewer_workflow",
                "run_quality_repair_batch",
                "run_gate_clearing_batch",
            ],
            invocation_kind="descriptor_only_current_owner_input_refs",
            callable_surface="stage_route_contract_and_hypothesis_portfolio_pack",
            output_refs=["external-learning:co_scientist:<action_type>"],
            role="hypothesis_portfolio_tournament_meta_review_refs_only_affordance",
        ),
        _capability(
            capability_id="display_pack_visual_capability",
            capability_family="display_pack",
            source_frameworks=["MAS Display Pack"],
            action_triggers=[
                "display_pack_orchestrate",
                "display_pack_figure_plan",
                "display_pack_preflight",
                "display_pack_render",
                "artifact_display_surface_materialization_required",
            ],
            invocation_kind="display_pack_agent",
            callable_surface="display_pack_agent.orchestrate",
            output_refs=["display_pack_agent_orchestration"],
            role="figure_intent_compilation_template_preflight_quality_floor_and_render_next_step",
        ),
    ]


def _standard_agent_feedback_loop_tail(
    *,
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
        "schema_version": SCHEMA_VERSION,
        "required_tail_keys": list(_STANDARD_AGENT_FEEDBACK_LOOP_TAIL_KEYS),
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
            for key in _STANDARD_AGENT_FEEDBACK_LOOP_TAIL_KEYS
            if key != "real_target_owner_accepted_answer_or_typed_blocker_scaleout_ref"
            or not owner_answer_refs
        ],
        "false_completion_blockers": list(_STANDARD_AGENT_FALSE_COMPLETION_BLOCKERS),
        "mas_repo_can_close_opl_family_tail": False,
        "opl_hosted_runtime_consumption_required": True,
        "counts_as_opl_family_completion": False,
    }


def _capability(
    *,
    capability_id: str,
    capability_family: str,
    source_frameworks: list[str],
    action_triggers: list[str],
    invocation_kind: str,
    callable_surface: str,
    output_refs: list[str],
    role: str,
) -> dict[str, Any]:
    return {
        "capability_id": capability_id,
        "capability_family": capability_family,
        "source_frameworks": source_frameworks,
        "trigger": DEFAULT_CURRENT_DELTA_TRIGGER,
        "action_triggers": action_triggers,
        "invocation_kind": invocation_kind,
        "callable_surface": callable_surface,
        "capability_ref": f"scientific-capability:{capability_id}",
        "role": role,
        "output_refs": output_refs,
        "refs_only": True,
        "body_included": False,
        "fail_open": True,
        "mainline_waits_for_capability": False,
        "external_runtime_dependency": False,
        "authority_boundary": _authority_boundary(),
    }


def _resolution_candidate(
    capability: Mapping[str, Any],
    *,
    action_type: str,
    current_owner_delta: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "capability_id": capability["capability_id"],
        "capability_family": capability["capability_family"],
        "source_frameworks": list(capability.get("source_frameworks") or []),
        "candidate_ref": f"scientific-capability:{capability['capability_id']}:{action_type}",
        "invocation_kind": capability["invocation_kind"],
        "callable_surface": capability["callable_surface"],
        "output_refs": list(capability.get("output_refs") or []),
        "role": capability["role"],
        "trigger_reason": _trigger_reason(capability, action_type=action_type, current_owner_delta=current_owner_delta),
        "refs_only": True,
        "body_included": False,
        "can_block_current_owner_action": False,
        "requires_explicit_invoke": True,
        "authority_boundary": _authority_boundary(),
    }


def _capability_matches(
    capability: Mapping[str, Any],
    *,
    action_type: str,
    requested_families: set[str],
) -> bool:
    family = _text(capability.get("capability_family"))
    if family in requested_families or _text(capability.get("capability_id")) in requested_families:
        return True
    triggers = set(_text_list(capability.get("action_triggers")))
    return "*" in triggers or action_type in triggers


def _trigger_reason(
    capability: Mapping[str, Any],
    *,
    action_type: str,
    current_owner_delta: Mapping[str, Any],
) -> str:
    requested = _text_set(current_owner_delta.get("capability_families")) | _text_set(
        current_owner_delta.get("route_required_ref_families")
    )
    if _text(capability.get("capability_family")) in requested:
        return "current_delta_requested_capability_family"
    if _text(capability.get("capability_id")) in requested:
        return "current_delta_requested_capability_id"
    if action_type in set(_text_list(capability.get("action_triggers"))):
        return "action_type_trigger"
    return "default_jit_affordance"


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


def _opl_capability_invocation_request(
    *,
    capability: Mapping[str, Any],
    current_owner_delta: Mapping[str, Any],
    study_root: Path | str | None,
    payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    delta = _mapping(current_owner_delta)
    request_payload = _mapping(payload)
    study_root_ref = _text(study_root)
    return {
        "surface_kind": "mas_opl_capability_invocation_request",
        "schema_version": SCHEMA_VERSION,
        "target_runtime_owner": "one-person-lab",
        "target_runtime_kind": "CapabilityRegistry",
        "request_owner": "med-autoscience",
        "authority_role": "capability_request_only",
        "capability_id": capability["capability_id"],
        "capability_family": capability["capability_family"],
        "invocation_kind": capability["invocation_kind"],
        "callable_surface": capability["callable_surface"],
        "study_root_ref": study_root_ref or None,
        "current_owner_delta_identity": _current_owner_summary(delta),
        "expected_output_refs": list(capability.get("output_refs") or []),
        "payload_ref": _text(request_payload.get("payload_ref")) or None,
        "mas_can_create_opl_outbox_record": False,
        "mas_can_create_opl_event": False,
        "mas_can_create_opl_stage_run": False,
        "mas_can_run_capability_actuator": False,
        "mainline_waits_for_capability": False,
    }


def _capability_request_projection(
    *,
    capability: Mapping[str, Any],
    current_owner_delta: Mapping[str, Any],
    runtime_request: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_scientific_capability_invocation_request_projection",
        "schema_version": SCHEMA_VERSION,
        "status": "opl_capability_request_pending",
        "capability_ref": capability["capability_ref"],
        "capability_id": capability["capability_id"],
        "capability_family": capability["capability_family"],
        "invocation_kind": capability["invocation_kind"],
        "refs_only": True,
        "body_included": False,
        "current_owner_delta_identity": _current_owner_summary(current_owner_delta),
        "output_refs": list(capability.get("output_refs") or []),
        "opl_capability_invocation_request": dict(runtime_request),
        "mas_local_capability_actuator": False,
        "mainline_waits_for_capability": False,
        "can_block_current_owner_action": False,
        "authority_boundary": _authority_boundary(),
    }


def _owner_response_refs(value: Mapping[str, Any] | None) -> dict[str, str | None]:
    refs = _mapping(value)
    return {
        key: (_text(refs.get(key)) or None)
        for key in _OWNER_RESPONSE_REF_KEYS
    }


def _no_forbidden_write_proof(invocation: Mapping[str, Any]) -> dict[str, Any]:
    result = _mapping(invocation.get("result"))
    study_root_text = _text(result.get("study_root_ref")) or _text(result.get("study_root"))
    existing_forbidden_refs: list[str] = []
    if study_root_text:
        study_root = Path(study_root_text).expanduser()
        for ref in _FORBIDDEN_PATH_ABSENCE_REFS:
            if (study_root / ref).exists():
                existing_forbidden_refs.append(ref)
    output_ref_set = set(_capability_output_refs(invocation))
    forbidden_ref_collisions = [
        ref for ref in _FORBIDDEN_WRITE_CHECK_REFS if ref in output_ref_set
    ]
    return {
        "checked_relative_refs": list(_FORBIDDEN_WRITE_CHECK_REFS),
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


def _current_owner_summary(delta: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "action_type": _text(delta.get("action_type")),
        "action_id": _text(delta.get("action_id")),
        "owner": _text(delta.get("owner")),
        "work_unit_id": _text(delta.get("work_unit_id")),
        "work_unit_fingerprint": _text(delta.get("work_unit_fingerprint")),
        "source_ref": _text(delta.get("source_ref")),
    }


def _evo_event(*, delta: Mapping[str, Any], payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "event_kind": "scientific_capability_registry_invoke",
        "source": "scientific_capability_registry",
        "study_id": _text(delta.get("study_id")),
        "quest_id": _text(delta.get("quest_id")),
        "current_owner_delta_ref": _text(delta.get("source_ref")),
        "current_owner_action_ref": _text(delta.get("source_ref")),
        "current_executable_owner_action": _current_owner_summary(delta),
        "allowed_tool_manifest_ref": _text(payload.get("allowed_tool_manifest_ref")),
        "executor_turn_summary_ref": _text(payload.get("executor_turn_summary_ref")),
        "subagent_summary_ref": _text(payload.get("subagent_summary_ref")),
        "receipt_or_typed_blocker_ref": _text(payload.get("receipt_or_typed_blocker_ref")),
        "prior_failed_path_memory_refs": _text_list(payload.get("prior_failed_path_memory_refs")),
    }


def _authority_boundary() -> dict[str, bool | str]:
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
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_artifact_authority": False,
        "can_close_stage": False,
    }


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


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _require_text(value: object, label: str) -> str:
    text = _text(value)
    if not text:
        raise ValueError(f"{label} is required")
    return text


def _text_list(value: object) -> list[str]:
    if isinstance(value, (str, Path)):
        text = _text(value)
        return [text] if text else []
    if not isinstance(value, (list, tuple, set)):
        return []
    return [text for item in value if (text := _text(item))]


def _text_set(value: object) -> set[str]:
    return set(_text_list(value))


def _dedupe_texts(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


__all__ = [
    "INVOCATION_SURFACE_KIND",
    "OWNER_CONSUMPTION_EVIDENCE_SURFACE_KIND",
    "RESOLUTION_SURFACE_KIND",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
    "build_scientific_capability_registry",
    "build_capability_owner_consumption_evidence",
    "invoke_scientific_capability",
    "resolve_scientific_capabilities",
]
