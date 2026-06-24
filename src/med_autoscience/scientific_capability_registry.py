from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience import external_learning_adoption_closure
from med_autoscience.runtime_protocol import evo_scientist_sidecar_refs
from med_autoscience.scholarskills_capability_modules import (
    SCHOLAR_DISPLAY_EXECUTION_RECEIPT_EXPECTATION,
    SCHOLAR_DISPLAY_EXECUTION_RECEIPT_REF_ALIASES as _SCHOLAR_DISPLAY_EXECUTION_RECEIPT_REF_ALIASES,
    SCHOLAR_DISPLAY_MODULE_ID,
    SCHOLARSKILLS_CAPABILITY_IDS,
    build_scholarskills_capabilities,
    scholarskills_execution_receipt_ref_aliases,
)
from med_autoscience.scholarskills_package_consumption import (
    build_candidate_artifact_owner_request_items,
    build_scholarskills_materialized_package_input,
)


SURFACE_KIND = "mas_scientific_capability_registry"
RESOLUTION_SURFACE_KIND = "mas_scientific_capability_resolution"
INVOCATION_SURFACE_KIND = "mas_scientific_capability_invocation"
OWNER_CONSUMPTION_EVIDENCE_SURFACE_KIND = (
    "mas_scientific_capability_owner_consumption_evidence"
)
SCHOLARSKILLS_OWNER_GATE_REQUEST_SURFACE_KIND = "mas_scholarskills_owner_gate_request"
SCHOLARSKILLS_OWNER_GATE_HANDOFF_SURFACE_KIND = "mas_scholarskills_owner_gate_handoff"
SCHEMA_VERSION = 1
DEFAULT_CURRENT_DELTA_TRIGGER = "current_delta_declares_or_implies_affordance_need"
_OWNER_RESPONSE_REF_KEYS = (
    "owner_receipt_ref",
    "typed_blocker_ref",
    "reviewer_receipt_ref",
    "route_back_evidence_ref",
)
_REQUIRED_OWNER_RESPONSE_SHAPES = (
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
NATURE_SKILLS_SOURCE_HEAD = "1cb9070fdd94929d5f267ce6585ac87e2cba60b3"
NATURE_FIGURE_CONTRACT_REFS = (
    (
        "external:nature-skills@"
        f"{NATURE_SKILLS_SOURCE_HEAD}:skills/nature-figure/SKILL.md"
    ),
    (
        "external:nature-skills@"
        f"{NATURE_SKILLS_SOURCE_HEAD}:skills/nature-figure/manifest.yaml"
    ),
    (
        "external:nature-skills@"
        f"{NATURE_SKILLS_SOURCE_HEAD}:skills/nature-figure/references/figure-contract.md"
    ),
    (
        "external:nature-skills@"
        f"{NATURE_SKILLS_SOURCE_HEAD}:skills/nature-figure/references/qa-contract.md"
    ),
    (
        "external:nature-skills@"
        f"{NATURE_SKILLS_SOURCE_HEAD}:skills/nature-figure/references/backend-selection.md"
    ),
)
NATURE_FIGURE_CURRENT_DELTA_TRIGGER_TERMS = (
    "figure",
    "display",
    "plotting",
    "stable plotting need",
    "stable_plotting_need",
)
NATURE_PAPER_MAINLINE_SECTION_REFS = (
    (
        "external:nature-skills@"
        f"{NATURE_SKILLS_SOURCE_HEAD}:skills/nature-writing/SKILL.md"
    ),
    (
        "external:nature-skills@"
        f"{NATURE_SKILLS_SOURCE_HEAD}:skills/nature-polishing/SKILL.md"
    ),
    (
        "external:nature-skills@"
        f"{NATURE_SKILLS_SOURCE_HEAD}:skills/nature-reader/SKILL.md"
    ),
    "med_autoscience.paper_mainline_section_source_map.build_paper_section_source_map_readback",
)
NATURE_PAPER_MAINLINE_CLAIM_SUPPORT_REFS = (
    (
        "external:nature-skills@"
        f"{NATURE_SKILLS_SOURCE_HEAD}:skills/nature-academic-search/SKILL.md"
    ),
    (
        "external:nature-skills@"
        f"{NATURE_SKILLS_SOURCE_HEAD}:skills/nature-citation/SKILL.md"
    ),
    "med_autoscience.paper_mainline_claim_support.build_claim_citation_support_matrix",
)
NATURE_PAPER_MAINLINE_REVIEWER_REPAIR_REFS = (
    (
        "external:nature-skills@"
        f"{NATURE_SKILLS_SOURCE_HEAD}:skills/nature-response/SKILL.md"
    ),
    (
        "external:nature-skills@"
        f"{NATURE_SKILLS_SOURCE_HEAD}:skills/nature-reviewer/SKILL.md"
    ),
    (
        "external:nature-skills@"
        f"{NATURE_SKILLS_SOURCE_HEAD}:skills/nature-reader/SKILL.md"
    ),
    "med_autoscience.paper_mainline_reviewer_repair.build_reviewer_repair_action_projection",
)
NATURE_PAPER_MAINLINE_TRIGGER_TERMS = (
    "paper mainline",
    "section source map",
    "section_contract",
    "draft_block_refs",
    "claim_refs",
    "evidence_refs",
    "source_map_refs",
    "reviewer_repair_refs",
)
NATURE_CLAIM_SUPPORT_TRIGGER_TERMS = (
    "claim citation support",
    "claim_support",
    "claim_support_matrix",
    "citation_refs",
    "support_grade",
    "source_tier",
)
NATURE_REVIEWER_REPAIR_TRIGGER_TERMS = (
    "reviewer repair",
    "reviewer_repair",
    "reviewer_repair_refs",
    "repair_action",
    "repair_action_candidates",
)
_CURRENT_DELTA_DECLARATION_KEYS = {
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
            "wildcard_action_triggers_auto_select": False,
            "wildcard_action_triggers_require_explicit_capability_request": True,
        },
        "capability_count": len(capabilities),
        "capabilities": capabilities,
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
                        for family, aliases in _scholarskills_execution_receipt_ref_aliases(
                            module_id
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
        invocation.update(
            {
                "status": "descriptor_only",
                "request_only": False,
                "descriptor_only": True,
                "opl_capability_runtime_required": False,
                "external_runner_invocation_allowed": False,
                "result": _descriptor_only_projection(
                    capability=capability,
                    current_owner_delta=delta,
                    runtime_request=runtime_request,
                ),
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
    capability_id = _text(invocation.get("capability_id"))
    if capability_id in SCHOLARSKILLS_CAPABILITY_IDS:
        materialized_package = _scholarskills_materialized_package_input(
            capability_id=capability_id,
            required_ref_families=_text_list(
                _mapping(
                    _capability_by_id(capability_id).get(
                        "execution_receipt_expectation"
                    )
                ).get("required_ref_families")
            ),
            execution_receipt_path=execution_receipt_path,
            materialized_package_manifest_path=materialized_package_manifest_path,
        )
        evidence.update(
            _scholarskills_execution_receipt_evidence(
                capability_id=capability_id,
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
            evidence=evidence,
            current_owner_delta=_mapping(current_owner_delta),
        )
        if owner_gate_readback:
            evidence.update(owner_gate_readback)
    return evidence


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
            capability_id="nature_figure_display_contract_refs",
            capability_family="figure_display_contract_refs",
            source_frameworks=[
                f"Yuan1z0825/nature-skills@{NATURE_SKILLS_SOURCE_HEAD}",
                "Nature Figure skill",
            ],
            action_triggers=[
                "display_pack_orchestrate",
                "display_pack_figure_plan",
                "display_pack_preflight",
                "display_pack_render",
                "artifact_display_surface_materialization_required",
            ],
            current_delta_trigger_terms=list(NATURE_FIGURE_CURRENT_DELTA_TRIGGER_TERMS),
            current_delta_trigger_reason="current_delta_declared_figure_display_need",
            invocation_kind="descriptor_only_current_owner_input_refs",
            callable_surface="descriptor_only:nature_figure_display_contract_refs",
            output_refs=list(NATURE_FIGURE_CONTRACT_REFS),
            contract_refs=list(NATURE_FIGURE_CONTRACT_REFS),
            role="nature_skills_figure_display_router_manifest_and_stable_plotting_refs",
        ),
        _capability(
            capability_id="nature_paper_section_source_map_readback",
            capability_family="paper_mainline_section_source_map",
            source_frameworks=[
                f"Yuan1z0825/nature-skills@{NATURE_SKILLS_SOURCE_HEAD}",
                "Nature Writing / Polishing / Reader skills",
            ],
            action_triggers=[
                "draft_manuscript_section",
                "run_quality_repair_batch",
                "return_to_ai_reviewer_workflow",
            ],
            current_delta_trigger_terms=list(NATURE_PAPER_MAINLINE_TRIGGER_TERMS),
            current_delta_trigger_reason="current_delta_declared_paper_mainline_section_need",
            invocation_kind="descriptor_only_current_owner_input_refs",
            callable_surface=(
                "med_autoscience.paper_mainline_section_source_map."
                "build_paper_section_source_map_readback"
            ),
            output_refs=["readback:mas_paper_section_source_map_readback"],
            contract_refs=list(NATURE_PAPER_MAINLINE_SECTION_REFS),
            role="section_contract_draft_block_source_map_reviewer_repair_refs_readback",
        ),
        _capability(
            capability_id="nature_claim_citation_support_matrix",
            capability_family="claim_citation_support_matrix",
            source_frameworks=[
                f"Yuan1z0825/nature-skills@{NATURE_SKILLS_SOURCE_HEAD}",
                "Nature Academic Search / Citation skills",
            ],
            action_triggers=[
                "draft_manuscript_section",
                "run_quality_repair_batch",
                "return_to_ai_reviewer_workflow",
            ],
            current_delta_trigger_terms=list(NATURE_CLAIM_SUPPORT_TRIGGER_TERMS),
            current_delta_trigger_reason="current_delta_declared_claim_support_need",
            invocation_kind="descriptor_only_current_owner_input_refs",
            callable_surface=(
                "med_autoscience.paper_mainline_claim_support."
                "build_claim_citation_support_matrix"
            ),
            output_refs=["readback:mas_claim_citation_support_matrix"],
            contract_refs=list(NATURE_PAPER_MAINLINE_CLAIM_SUPPORT_REFS),
            role="claim_evidence_citation_support_grade_refs_only_matrix",
        ),
        _capability(
            capability_id="nature_reviewer_repair_action_projection",
            capability_family="reviewer_repair_action_projection",
            source_frameworks=[
                f"Yuan1z0825/nature-skills@{NATURE_SKILLS_SOURCE_HEAD}",
                "Nature Response / Reviewer / Reader skills",
            ],
            action_triggers=[
                "run_quality_repair_batch",
                "return_to_ai_reviewer_workflow",
                "run_gate_clearing_batch",
            ],
            current_delta_trigger_terms=list(NATURE_REVIEWER_REPAIR_TRIGGER_TERMS),
            current_delta_trigger_reason="current_delta_declared_reviewer_repair_need",
            invocation_kind="descriptor_only_current_owner_input_refs",
            callable_surface=(
                "med_autoscience.paper_mainline_reviewer_repair."
                "build_reviewer_repair_action_projection"
            ),
            output_refs=["readback:mas_reviewer_repair_action_projection"],
            contract_refs=list(NATURE_PAPER_MAINLINE_REVIEWER_REPAIR_REFS),
            role="ai_reviewer_comment_to_typed_repair_action_candidate_projection",
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
        *_scholarskills_capabilities(),
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


def _scholarskills_capabilities() -> list[dict[str, Any]]:
    return build_scholarskills_capabilities(
        schema_version=SCHEMA_VERSION,
        default_trigger=DEFAULT_CURRENT_DELTA_TRIGGER,
        authority_boundary=_authority_boundary(),
        display_trigger_terms=NATURE_FIGURE_CURRENT_DELTA_TRIGGER_TERMS,
    )


def _capability(
    *,
    capability_id: str,
    capability_family: str,
    module_id: str | None = None,
    source_frameworks: list[str],
    action_triggers: list[str],
    invocation_kind: str,
    callable_surface: str,
    output_refs: list[str],
    role: str,
    current_delta_trigger_terms: list[str] | None = None,
    current_delta_trigger_reason: str | None = None,
    contract_refs: list[str] | None = None,
    descriptor_refs: list[str] | None = None,
    dependency_profile_refs: list[str] | None = None,
    run_context_refs: list[str] | None = None,
    artifact_refs: list[str] | None = None,
    execution_receipt_expectation: Mapping[str, Any] | None = None,
    owner_consumption_boundary: Mapping[str, Any] | None = None,
    bridged_capability_refs: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
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
    if module_id:
        payload["module_id"] = module_id
    if current_delta_trigger_terms:
        payload["current_delta_trigger_terms"] = list(current_delta_trigger_terms)
    if current_delta_trigger_reason:
        payload["current_delta_trigger_reason"] = current_delta_trigger_reason
    if contract_refs:
        payload["contract_refs"] = list(contract_refs)
    if descriptor_refs:
        payload["descriptor_refs"] = list(descriptor_refs)
    if dependency_profile_refs:
        payload["dependency_profile_refs"] = list(dependency_profile_refs)
    if run_context_refs:
        payload["run_context_refs"] = list(run_context_refs)
    if artifact_refs:
        payload["artifact_refs"] = list(artifact_refs)
    if execution_receipt_expectation:
        payload["execution_receipt_expectation"] = dict(execution_receipt_expectation)
    if owner_consumption_boundary:
        payload["owner_consumption_boundary"] = dict(owner_consumption_boundary)
    if bridged_capability_refs:
        payload["bridged_capability_refs"] = list(bridged_capability_refs)
    if invocation_kind == "descriptor_only_current_owner_input_refs":
        payload["descriptor_only"] = True
        payload["external_runner_invocation_allowed"] = False
    if "*" in action_triggers:
        payload["wildcard_action_trigger_policy"] = {
            "auto_select": False,
            "requires_explicit_capability_request": True,
            "reason": "support_or_diagnostic_wildcards_must_not_become_mas_private_selectors",
        }
    return payload


def _resolution_candidate(
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
        "trigger_reason": _trigger_reason(capability, action_type=action_type, current_owner_delta=current_owner_delta),
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
            _mapping(capability.get("execution_receipt_expectation"))
        ),
        "owner_consumption_boundary": dict(
            _mapping(capability.get("owner_consumption_boundary"))
        ),
        "bridged_capability_refs": list(capability.get("bridged_capability_refs") or []),
        "readback": _capability_readback(capability),
        "authority_boundary": _authority_boundary(),
    }
    module_id = _text(capability.get("module_id"))
    if module_id:
        candidate["module_id"] = module_id
    wildcard_policy = _mapping(capability.get("wildcard_action_trigger_policy"))
    if wildcard_policy:
        candidate["wildcard_action_trigger_policy"] = dict(wildcard_policy)
    return candidate


def _capability_matches(
    capability: Mapping[str, Any],
    *,
    action_type: str,
    requested_families: set[str],
    current_owner_delta: Mapping[str, Any],
) -> bool:
    family = _text(capability.get("capability_family"))
    if family in requested_families or _text(capability.get("capability_id")) in requested_families:
        return True
    triggers = set(_text_list(capability.get("action_triggers")))
    if action_type in triggers:
        return True
    return _current_delta_declares_terms(
        current_owner_delta,
        terms=_text_list(capability.get("current_delta_trigger_terms")),
    )


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
    if _current_delta_declares_terms(
        current_owner_delta,
        terms=_text_list(capability.get("current_delta_trigger_terms")),
    ):
        return (
            _text(capability.get("current_delta_trigger_reason"))
            or "current_delta_declared_capability_need"
        )
    return "default_jit_affordance"


def _capability_readback(capability: Mapping[str, Any]) -> dict[str, Any]:
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
    module_id = _text(capability.get("module_id"))
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
    execution_receipt_expectation = _mapping(
        capability.get("execution_receipt_expectation")
    )
    if execution_receipt_expectation:
        readback["execution_receipt_expectation"] = dict(execution_receipt_expectation)
    owner_consumption_boundary = _mapping(capability.get("owner_consumption_boundary"))
    if owner_consumption_boundary:
        readback["owner_consumption_boundary"] = dict(owner_consumption_boundary)
    if module_id:
        readback["authority_false_flags"] = _authority_false_flags()
    return readback


def _current_delta_declares_terms(
    current_owner_delta: Mapping[str, Any],
    *,
    terms: list[str],
) -> bool:
    if not terms:
        return False
    haystack = " ".join(_current_delta_declaration_texts(current_owner_delta)).lower()
    return any(term.lower() in haystack for term in terms)


def _current_delta_declaration_texts(value: object) -> list[str]:
    if isinstance(value, Mapping):
        texts: list[str] = []
        for key, item in value.items():
            if key in _CURRENT_DELTA_DECLARATION_KEYS or str(key).endswith(
                ("_ref", "_refs", "_need", "_needs", "_kind", "_surface")
            ):
                texts.append(str(key))
                texts.extend(_current_delta_declaration_texts(item))
            elif isinstance(item, Mapping):
                texts.extend(_current_delta_declaration_texts(item))
        return texts
    if isinstance(value, (list, tuple, set)):
        texts = []
        for item in value:
            texts.extend(_current_delta_declaration_texts(item))
        return texts
    text = _text(value)
    return [text] if text else []


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


def _descriptor_only_projection(
    *,
    capability: Mapping[str, Any],
    current_owner_delta: Mapping[str, Any],
    runtime_request: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_scientific_capability_descriptor_only_projection",
        "schema_version": SCHEMA_VERSION,
        "status": "descriptor_only",
        "capability_ref": capability["capability_ref"],
        "capability_id": capability["capability_id"],
        "capability_family": capability["capability_family"],
        "invocation_kind": capability["invocation_kind"],
        "refs_only": True,
        "descriptor_only": True,
        "request_only": False,
        "body_included": False,
        "current_owner_delta_identity": _current_owner_summary(current_owner_delta),
        "output_refs": list(capability.get("output_refs") or []),
        "contract_refs": list(capability.get("contract_refs") or []),
        "readback": _capability_readback(capability),
        "opl_capability_invocation_request": dict(runtime_request),
        "mas_local_capability_actuator": False,
        "external_runner_invocation_allowed": False,
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


def _scholar_display_execution_receipt_evidence(
    *,
    execution_receipt: Mapping[str, Any] | str | None,
    execution_receipt_refs: Mapping[str, Any] | None,
    explicit_refs: Mapping[str, Any],
) -> dict[str, Any]:
    refs = _scholar_display_execution_receipt_refs(
        execution_receipt=execution_receipt,
        execution_receipt_refs=execution_receipt_refs,
        explicit_refs=explicit_refs,
    )
    required = _text_list(
        SCHOLAR_DISPLAY_EXECUTION_RECEIPT_EXPECTATION.get("required_ref_families")
    )
    observed = [
        family
        for family in required
        if _text(refs.get(family))
    ]
    missing = [
        family
        for family in required
        if family not in observed
    ]
    execution_receipt_ref = _text(refs.get("execution_receipt_ref")) or None
    status = "complete" if not missing else "missing_required_refs"
    return {
        "execution_receipt_ref": execution_receipt_ref,
        "execution_receipt_refs": {
            family: _text(refs.get(family))
            for family in required
            if _text(refs.get(family))
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


def _scholarskills_execution_receipt_evidence(
    *,
    capability_id: str,
    execution_receipt: Mapping[str, Any] | str | None,
    execution_receipt_refs: Mapping[str, Any] | None,
    explicit_refs: Mapping[str, Any],
) -> dict[str, Any]:
    capability = _capability_by_id(capability_id)
    expectation = _mapping(capability.get("execution_receipt_expectation"))
    required = _text_list(expectation.get("required_ref_families"))
    refs = _scholarskills_execution_receipt_refs(
        capability_id=capability_id,
        execution_receipt=execution_receipt,
        execution_receipt_refs=execution_receipt_refs,
        explicit_refs=explicit_refs,
    )
    observed = [family for family in required if _text(refs.get(family))]
    missing = [family for family in required if family not in observed]
    execution_receipt_ref = _text(refs.get("execution_receipt_ref")) or None
    status = "complete" if not missing else "missing_required_refs"
    return {
        "execution_receipt_ref": execution_receipt_ref,
        "execution_receipt_refs": {
            family: _text(refs.get(family))
            for family in required
            if _text(refs.get(family))
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


def _scholarskills_execution_receipt_refs(
    *,
    capability_id: str,
    execution_receipt: Mapping[str, Any] | str | None,
    execution_receipt_refs: Mapping[str, Any] | None,
    explicit_refs: Mapping[str, Any],
) -> dict[str, str]:
    raw: dict[str, Any] = {}
    if isinstance(execution_receipt, str):
        raw["execution_receipt_ref"] = execution_receipt
    else:
        raw.update(_mapping(execution_receipt))
    raw.update(_mapping(execution_receipt_refs))
    raw.update({key: value for key, value in explicit_refs.items() if _text(value)})

    nested_refs = _mapping(raw.get("refs"))
    if nested_refs:
        raw.update({key: value for key, value in nested_refs.items() if key not in raw})
    nested_execution_refs = _mapping(raw.get("execution_receipt_refs"))
    if nested_execution_refs:
        raw.update(
            {key: value for key, value in nested_execution_refs.items() if key not in raw}
        )

    result: dict[str, str] = {}
    execution_receipt_ref = (
        _text(raw.get("execution_receipt_ref"))
        or _text(raw.get("receipt_ref"))
        or _text(raw.get("receipt_uri"))
    )
    if execution_receipt_ref:
        result["execution_receipt_ref"] = execution_receipt_ref
    for family, aliases in _scholarskills_execution_receipt_ref_aliases(
        capability_id
    ).items():
        for alias in aliases:
            ref = _text(raw.get(alias))
            if ref:
                result[family] = ref
                break
    return result


def _scholarskills_materialized_package_input(
    *,
    capability_id: str,
    required_ref_families: list[str],
    execution_receipt_path: Path | str | None,
    materialized_package_manifest_path: Path | str | None,
) -> dict[str, Any]:
    return build_scholarskills_materialized_package_input(
        capability_id=capability_id,
        required_ref_families=required_ref_families,
        execution_receipt_path=execution_receipt_path,
        materialized_package_manifest_path=materialized_package_manifest_path,
    )


def _scholarskills_owner_gate_readback(
    *,
    evidence: Mapping[str, Any],
    current_owner_delta: Mapping[str, Any],
) -> dict[str, Any]:
    package = _mapping(evidence.get("materialized_package_consumption"))
    if not _scholarskills_owner_gate_requestable(evidence=evidence, package=package):
        return {}
    request = _scholarskills_owner_gate_request(
        evidence=evidence,
        package=package,
        current_owner_delta=current_owner_delta,
    )
    return {
        "owner_gate_request": request,
        "owner_gate_handoff": _scholarskills_owner_gate_handoff(
            request=request,
            package=package,
        ),
        "required_owner_response_shapes": [
            dict(shape) for shape in _REQUIRED_OWNER_RESPONSE_SHAPES
        ],
    }


def _scholarskills_owner_gate_requestable(
    *,
    evidence: Mapping[str, Any],
    package: Mapping[str, Any],
) -> bool:
    return (
        bool(package)
        and _text(evidence.get("execution_receipt_status")) == "complete"
        and package.get("authority_flags_false") is True
        and not _text_list(package.get("forbidden_written_file_collisions"))
        and not _text_list(package.get("mas_consumer_written_files"))
    )


def _scholarskills_owner_gate_request(
    *,
    evidence: Mapping[str, Any],
    package: Mapping[str, Any],
    current_owner_delta: Mapping[str, Any],
) -> dict[str, Any]:
    candidate_artifacts = _candidate_artifact_owner_request_items(package)
    return {
        "surface_kind": SCHOLARSKILLS_OWNER_GATE_REQUEST_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "request_status": "ready_for_owner_gate_review",
        "request_role": "non_authoritative_scholarskills_candidate_review_request",
        "non_authoritative_request": True,
        "refs_only": True,
        "capability_id": _text(evidence.get("capability_id")),
        "capability_family": _text(evidence.get("capability_family")),
        "module_id": _text(package.get("module_id")) or _text(evidence.get("capability_id")),
        "current_owner_delta_identity": _current_owner_summary(current_owner_delta),
        "execution_receipt_ref": _text(evidence.get("execution_receipt_ref")) or None,
        "execution_receipt_status": _text(evidence.get("execution_receipt_status")),
        "execution_receipt_refs": dict(_mapping(evidence.get("execution_receipt_refs"))),
        "observed_execution_receipt_ref_families": _text_list(
            evidence.get("observed_execution_receipt_ref_families")
        ),
        "materialized_package_manifest_path": _text(package.get("manifest_path")) or None,
        "materialized_package_execution_receipt_path": _text(
            package.get("execution_receipt_path")
        )
        or None,
        "materialized_package_sha256": _text(package.get("sha256")) or None,
        "materialized_package_written_files": _text_list(package.get("written_files")),
        "candidate_artifacts": candidate_artifacts,
        "candidate_artifact_count": len(candidate_artifacts),
        "candidate_artifact_missing_inputs": _text_list(
            package.get("candidate_artifact_missing_inputs")
        ),
        "required_owner_response_shapes": [
            _text(shape["shape"]) for shape in _REQUIRED_OWNER_RESPONSE_SHAPES
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
        "authority_boundary": _authority_boundary(),
    }


def _scholarskills_owner_gate_handoff(
    *,
    request: Mapping[str, Any],
    package: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface_kind": SCHOLARSKILLS_OWNER_GATE_HANDOFF_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "handoff_status": "ready_for_owner_gate_review",
        "handoff_role": "mas_owner_gate_review_handoff",
        "source_request_ref": "inline:owner_gate_request",
        "next_owner": "MAS owner gate",
        "capability_id": _text(request.get("capability_id")),
        "module_id": _text(request.get("module_id")),
        "candidate_artifacts": _candidate_artifact_owner_request_items(request),
        "candidate_artifact_missing_inputs": _text_list(
            request.get("candidate_artifact_missing_inputs")
        ),
        "required_owner_response_shapes": [
            dict(shape) for shape in _REQUIRED_OWNER_RESPONSE_SHAPES
        ],
        "forbidden_authority_writes_absent": (
            package.get("authority_flags_false") is True
            and not _text_list(package.get("forbidden_written_file_collisions"))
        ),
        "mas_consumer_written_files": [],
        "counts_as_progress": False,
        "counts_as_paper_truth": False,
        "counts_as_owner_receipt": False,
    }


def _candidate_artifact_owner_request_items(
    payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return build_candidate_artifact_owner_request_items(payload)


def _scholarskills_execution_receipt_ref_aliases(
    capability_id: str,
) -> dict[str, tuple[str, ...]]:
    capability = _capability_by_id(capability_id)
    expectation = _mapping(capability.get("execution_receipt_expectation"))
    return scholarskills_execution_receipt_ref_aliases(
        capability_id=capability_id,
        required_ref_families=_text_list(expectation.get("required_ref_families")),
    )


def _scholar_display_execution_receipt_refs(
    *,
    execution_receipt: Mapping[str, Any] | str | None,
    execution_receipt_refs: Mapping[str, Any] | None,
    explicit_refs: Mapping[str, Any],
) -> dict[str, str]:
    raw: dict[str, Any] = {}
    if isinstance(execution_receipt, str):
        raw["execution_receipt_ref"] = execution_receipt
    else:
        raw.update(_mapping(execution_receipt))
    raw.update(_mapping(execution_receipt_refs))
    raw.update({key: value for key, value in explicit_refs.items() if _text(value)})

    nested_refs = _mapping(raw.get("refs"))
    if nested_refs:
        raw.update({key: value for key, value in nested_refs.items() if key not in raw})
    nested_execution_refs = _mapping(raw.get("execution_receipt_refs"))
    if nested_execution_refs:
        raw.update(
            {key: value for key, value in nested_execution_refs.items() if key not in raw}
        )

    result: dict[str, str] = {}
    execution_receipt_ref = (
        _text(raw.get("execution_receipt_ref"))
        or _text(raw.get("receipt_ref"))
        or _text(raw.get("receipt_uri"))
    )
    if execution_receipt_ref:
        result["execution_receipt_ref"] = execution_receipt_ref
    for family, aliases in _SCHOLAR_DISPLAY_EXECUTION_RECEIPT_REF_ALIASES.items():
        for alias in aliases:
            ref = _text(raw.get(alias))
            if ref:
                result[family] = ref
                break
    return result


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
        "can_authorize_provider_admission": False,
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


def _authority_false_flags() -> dict[str, bool]:
    authority = _authority_boundary()
    return {
        key: value
        for key, value in authority.items()
        if key.startswith("can_") and value is False
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


def _merge_mappings(*values: object) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for value in values:
        result.update(_mapping(value))
    return result


def _merge_execution_receipt_input(*values: object) -> Mapping[str, Any] | str | None:
    result: dict[str, Any] = {}
    string_ref: str | None = None
    for value in values:
        if isinstance(value, str):
            string_ref = value
            continue
        result.update(_mapping(value))
    return result or string_ref


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
