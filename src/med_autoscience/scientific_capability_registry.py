from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience import external_learning_adoption_closure
from med_autoscience.runtime_protocol import evo_scientist_sidecar_refs
from med_autoscience.scholarskills_local_install import (
    build_scholarskills_local_install_template,
)
from med_autoscience.scholarskills_capability_modules import (
    SCHOLAR_DISPLAY_EXECUTION_RECEIPT_EXPECTATION,
    SCHOLAR_DISPLAY_EXECUTION_RECEIPT_REF_ALIASES as _SCHOLAR_DISPLAY_EXECUTION_RECEIPT_REF_ALIASES,
    SCHOLAR_DISPLAY_MODULE_ID,
    SCHOLARSKILLS_CAPABILITY_IDS,
    build_scholarskills_capabilities,
    scholarskills_execution_receipt_ref_aliases,
)
from med_autoscience.scientific_capability_registry_parts import (
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


SURFACE_KIND = "mas_scientific_capability_registry"
SUMMARY_SURFACE_KIND = "mas_scientific_capability_registry_summary"
INVENTORY_SURFACE_KIND = "mas_scientific_capability_inventory"
RESOLUTION_SURFACE_KIND = "mas_scientific_capability_resolution"
INVOCATION_SURFACE_KIND = "mas_scientific_capability_invocation"
SCHEMA_VERSION = 1
DEFAULT_CURRENT_DELTA_TRIGGER = "current_delta_declares_or_implies_affordance_need"
NATURE_SKILLS_SOURCE_HEAD = "1cb9070fdd94929d5f267ce6585ac87e2cba60b3"
ACADEMICFORGE_SOURCE_HEAD = "54a2f333973147a1fd703caea6f12252e1f227d6"
OPENSCIENCE_SOURCE_HEAD = "2200ad2ec4e2ac7c7ff59c5dcdfaeb0b9a5fda66"
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
OPENSCIENCE_ARTIFACT_PROVENANCE_TRIGGER_TERMS = (
    "artifact graph",
    "artifact_graph",
    "artifact provenance",
    "claim warning",
    "claim_warning",
    "annotation regeneration",
    "annotation_regeneration",
    "project ledger",
    "project_ledger",
    "connector provenance",
    "data flow",
    "data-flow",
    "source lineage",
)
ACADEMICFORGE_SKILL_FIRST_REFS = (
    (
        "external:AcademicForge@"
        f"{ACADEMICFORGE_SOURCE_HEAD}:skills/claude-science/figure-style/SKILL.md"
    ),
    (
        "external:AcademicForge@"
        f"{ACADEMICFORGE_SOURCE_HEAD}:skills/claude-science/figure-composer/SKILL.md"
    ),
    (
        "external:AcademicForge@"
        f"{ACADEMICFORGE_SOURCE_HEAD}:skills/claude-science/paper-narrative/SKILL.md"
    ),
    (
        "external:AcademicForge@"
        f"{ACADEMICFORGE_SOURCE_HEAD}:skills/claude-science/literature-review/SKILL.md"
    ),
    (
        "external:AcademicForge@"
        f"{ACADEMICFORGE_SOURCE_HEAD}:skills/claude-science/pdf-explore/SKILL.md"
    ),
    "external_repo:mas-scholar-skills/skills/medical-figure-design/SKILL.md",
    "external_repo:mas-scholar-skills/skills/medical-figure-style/SKILL.md",
    "external_repo:mas-scholar-skills/skills/medical-figure-composer/SKILL.md",
    "external_repo:mas-scholar-skills/skills/medical-manuscript-writing/SKILL.md",
    "external_repo:mas-scholar-skills/skills/medical-manuscript-review/SKILL.md",
    "external_repo:mas-scholar-skills/skills/medical-research-lit/SKILL.md",
    "external_repo:mas-scholar-skills/skills/research-pdf-evidence-explorer/SKILL.md",
)
ACADEMICFORGE_LIFE_SCIENCE_SPECIALIST_REFS = (
    (
        "external:AcademicForge@"
        f"{ACADEMICFORGE_SOURCE_HEAD}:skills/claude-science/alphafold2/SKILL.md"
    ),
    (
        "external:AcademicForge@"
        f"{ACADEMICFORGE_SOURCE_HEAD}:skills/claude-science/boltz/SKILL.md"
    ),
    (
        "external:AcademicForge@"
        f"{ACADEMICFORGE_SOURCE_HEAD}:skills/claude-science/scgpt/SKILL.md"
    ),
    (
        "external:AcademicForge@"
        f"{ACADEMICFORGE_SOURCE_HEAD}:skills/claude-science/scvi-tools/SKILL.md"
    ),
    "external_repo:mas-scholar-skills/skills/medical-structural-biology/SKILL.md",
    "external_repo:mas-scholar-skills/skills/medical-protein-design/SKILL.md",
    "external_repo:mas-scholar-skills/skills/medical-genomics-foundation-models/SKILL.md",
    "external_repo:mas-scholar-skills/skills/medical-single-cell-modeling/SKILL.md",
    "external_repo:mas-scholar-skills/skills/medical-indication-dossier/SKILL.md",
)
ACADEMICFORGE_COMPUTE_SKILL_REFS = (
    (
        "external:AcademicForge@"
        f"{ACADEMICFORGE_SOURCE_HEAD}:skills/claude-science/compute-env-setup/SKILL.md"
    ),
    (
        "external:AcademicForge@"
        f"{ACADEMICFORGE_SOURCE_HEAD}:skills/claude-science/remote-compute-ssh/SKILL.md"
    ),
    (
        "external:AcademicForge@"
        f"{ACADEMICFORGE_SOURCE_HEAD}:skills/claude-science/remote-compute-modal/SKILL.md"
    ),
    (
        "external:AcademicForge@"
        f"{ACADEMICFORGE_SOURCE_HEAD}:skills/claude-science/managed-model-endpoints/SKILL.md"
    ),
    (
        "external:AcademicForge@"
        f"{ACADEMICFORGE_SOURCE_HEAD}:skills/claude-science/using-model-endpoint/SKILL.md"
    ),
    "external_repo:mas-scholar-skills/skills/scientific-compute-runner/SKILL.md",
    "opl:runway:execution-receipt",
    "opl:connect:provider-or-endpoint-receipt",
)
ACADEMICFORGE_TRIGGER_TERMS = (
    "claude science",
    "AcademicForge",
    "skill first",
    "skill-first",
    "AI First",
    "contract light",
    "figure composer",
    "paper narrative",
    "pdf explore",
)
LIFE_SCIENCE_SPECIALIST_TRIGGER_TERMS = (
    "structure prediction",
    "protein design",
    "protein embedding",
    "single-cell",
    "scRNA",
    "genomics foundation model",
    "indication dossier",
)
COMPUTE_SKILL_TRIGGER_TERMS = (
    "remote compute",
    "SLURM",
    "Modal",
    "model endpoint",
    "weight cache",
    "compute environment",
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
            "wildcard_action_triggers_auto_select": False,
            "wildcard_action_triggers_require_explicit_capability_request": True,
        },
        "capability_count": len(capabilities),
        "capabilities": capabilities,
        "scholarskills_local_install": build_scholarskills_local_install_template(),
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
            capability_id="openscience_artifact_provenance_advisory",
            capability_family="workspace_provenance_advisory",
            source_frameworks=[
                f"ai4s-research/open-science@{OPENSCIENCE_SOURCE_HEAD}",
                "OpenScience@2200ad2",
            ],
            action_triggers=[
                "artifact_display_surface_materialization_required",
                "return_to_ai_reviewer_workflow",
                "run_gate_clearing_batch",
                "run_quality_repair_batch",
                "unit_harmonized_external_validation_rerun",
            ],
            current_delta_trigger_terms=list(
                OPENSCIENCE_ARTIFACT_PROVENANCE_TRIGGER_TERMS
            ),
            current_delta_trigger_reason="current_delta_declared_openscience_artifact_provenance_need",
            invocation_kind="external_learning_sidecar",
            callable_surface=external_learning_adoption_closure.SIDECAR_CALLABLE_SURFACE,
            output_refs=[external_learning_adoption_closure.SIDECAR_RESULT_RELATIVE_PATH.as_posix()],
            role=(
                "artifact_graph_claim_warning_annotation_regeneration_ledger_"
                "connector_and_data_flow_refs_only_advisory"
            ),
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
            capability_id="academicforge_claude_science_skill_first_pack",
            capability_family="skill_first_professional_capability_pack",
            source_frameworks=[
                f"HughYau/AcademicForge@{ACADEMICFORGE_SOURCE_HEAD}",
                "Claude Science built-in skills",
                "MAS Scholar Skills",
            ],
            action_triggers=[
                "draft_manuscript_section",
                "run_quality_repair_batch",
                "return_to_ai_reviewer_workflow",
                "artifact_display_surface_materialization_required",
            ],
            current_delta_trigger_terms=list(ACADEMICFORGE_TRIGGER_TERMS),
            current_delta_trigger_reason="current_delta_declared_skill_first_professional_capability_need",
            invocation_kind="descriptor_only_current_owner_input_refs",
            callable_surface="descriptor_only:academicforge_claude_science_skill_first_pack",
            output_refs=[
                "external_repo:mas-scholar-skills/skills/<skill_id>/SKILL.md",
                "readback:mas_scholarskills_local_install",
            ],
            contract_refs=[
                "contracts/academicforge_claude_science_learning_adoption.json",
                "docs/runtime/control/external_learning_adoption_closure.md#academicforge-claude-science",
            ],
            descriptor_refs=list(ACADEMICFORGE_SKILL_FIRST_REFS),
            role=(
                "skill_first_ai_playbook_for_publication_figures_literature_pdf_"
                "paper_narrative_and_professional_specialist_handoff"
            ),
        ),
        _capability(
            capability_id="academicforge_life_science_specialist_skills",
            capability_family="life_science_specialist_skill_pack",
            source_frameworks=[
                f"HughYau/AcademicForge@{ACADEMICFORGE_SOURCE_HEAD}",
                "Claude Science structural biology / genomics / single-cell skills",
                "MAS Scholar Skills optional specialist pack",
            ],
            action_triggers=[
                "unit_harmonized_external_validation_rerun",
                "source_specialist_evidence_required",
                "analysis_specialist_evidence_required",
            ],
            current_delta_trigger_terms=list(LIFE_SCIENCE_SPECIALIST_TRIGGER_TERMS),
            current_delta_trigger_reason="current_delta_declared_life_science_specialist_skill_need",
            invocation_kind="descriptor_only_current_owner_input_refs",
            callable_surface="descriptor_only:academicforge_life_science_specialist_skills",
            output_refs=[
                "candidate:structure_or_omics_artifact_refs",
                "candidate:specialist_execution_receipt_refs",
                "candidate:owner_gate_handoff_ref",
            ],
            contract_refs=[
                "contracts/academicforge_claude_science_learning_adoption.json#/specialist_skill_pack",
            ],
            descriptor_refs=list(ACADEMICFORGE_LIFE_SCIENCE_SPECIALIST_REFS),
            role=(
                "optional_external_specialist_skills_for_structure_prediction_"
                "protein_design_genomics_single_cell_and_indication_dossiers"
            ),
        ),
        _capability(
            capability_id="academicforge_scientific_compute_runner_skill",
            capability_family="scientific_compute_runner",
            source_frameworks=[
                f"HughYau/AcademicForge@{ACADEMICFORGE_SOURCE_HEAD}",
                "Claude Science compute / endpoint skills",
                "OPL Runway / Connect",
            ],
            action_triggers=[
                "unit_harmonized_external_validation_rerun",
                "analysis_specialist_evidence_required",
                "remote_compute_required",
            ],
            current_delta_trigger_terms=list(COMPUTE_SKILL_TRIGGER_TERMS),
            current_delta_trigger_reason="current_delta_declared_scientific_compute_runner_need",
            invocation_kind="descriptor_only_current_owner_input_refs",
            callable_surface="descriptor_only:opl_runway_connect_scientific_compute_runner_skill",
            output_refs=[
                "candidate:opl_runway_execution_receipt_ref",
                "candidate:opl_connect_provider_receipt_ref",
                "candidate:dependency_profile_ref",
            ],
            contract_refs=[
                "contracts/academicforge_claude_science_learning_adoption.json#/compute_substrate",
                "docs/runtime/projections/runtime_capability_matrix.md#opl-capability-runtime--scholarskills-投影",
            ],
            descriptor_refs=list(ACADEMICFORGE_COMPUTE_SKILL_REFS),
            role=(
                "skill_first_compute_diagnostic_playbook_with_opl_owned_provider_"
                "credential_submit_wait_harvest_and_endpoint_receipts"
            ),
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
