from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.scholarskills_package_consumption import (
    build_scholarskills_materialized_package_input,
)
from med_autoscience.scholarskills_local_install import (
    SCHOLARSKILLS_LOCAL_INSTALL_READBACK_REF,
    SCHOLARSKILLS_MAS_PROGRAM_REPO_MIRROR_PATH,
    SCHOLARSKILLS_SOURCE_REPO_REF,
    build_scholarskills_local_install_template,
)


SCHOLAR_DISPLAY_MODULE_ID = "opl.scholarskills.display"
SCHOLARSKILLS_MODULE_NAMES = (
    "display",
    "tables",
    "stats",
    "lit",
    "write",
    "review",
    "submit",
    "data",
)
SCHOLARSKILLS_CAPABILITY_IDS = tuple(
    f"opl.scholarskills.{name}" for name in SCHOLARSKILLS_MODULE_NAMES
)
SCHOLARSKILLS_REAL_SKILL_BACKED_MODULES = {
    "display": "medical-figure-design",
    "lit": "medical-research-lit",
    "write": "medical-manuscript-writing",
    "review": "medical-manuscript-review",
    "stats": "medical-statistical-review",
    "tables": "medical-table-design",
    "submit": "medical-submission-prep",
    "data": "medical-data-governance",
}
SCHOLARSKILLS_NON_DISPLAY_MIGRATION_AUDIT = {
    "lit": {
        "migration_priority": "P0",
        "mas_retained_authority": [
            "claim_boundary",
            "citation_accept_reject",
            "evidence_ledger_acceptance",
        ],
    },
    "tables": {
        "migration_priority": "P0",
        "mas_retained_authority": [
            "table_acceptance_for_current_paper",
            "reporting_guideline_blocker",
            "submission_facing_authority",
        ],
    },
    "stats": {
        "migration_priority": "P0",
        "mas_retained_authority": [
            "medical_question_fit",
            "result_to_manuscript_gate",
            "analysis_campaign_closeout",
        ],
    },
    "submit": {
        "migration_priority": "P0",
        "mas_retained_authority": [
            "submission_readiness",
            "current_package_authority",
            "irreversible_submission_action",
        ],
    },
    "write": {
        "migration_priority": "P1",
        "mas_retained_authority": [
            "manuscript_truth",
            "claim_accept_reject",
            "publication_eval",
        ],
    },
    "review": {
        "migration_priority": "P1",
        "mas_retained_authority": [
            "final_quality_verdict",
            "route_back_owner_decision",
            "typed_blocker",
        ],
    },
    "data": {
        "migration_priority": "P1",
        "mas_retained_authority": [
            "source_readiness_verdict",
            "study_binding",
            "irreversible_data_mutation_authorization",
        ],
    },
}
SCHOLARSKILLS_OPERATING_MODEL_REF = (
    "docs/runtime/designs/mas_opl_capability_module_operating_model.md"
)
SCHOLAR_DISPLAY_DESCRIPTOR_REFS = (
    "scientific-capability:display_pack_visual_capability",
    "contracts/display-pack-contract.v2.json",
    "med_autoscience.display_pack_v2_contract.load_display_pack_v2_contract",
    "med_autoscience.display_pack_agent.display_pack_capability_discover",
    "med_autoscience.display_pack_agent.display_pack_figure_plan",
    "med_autoscience.display_pack_agent.display_pack_preflight",
    "med_autoscience.display_pack_agent.display_pack_render",
)
SCHOLAR_DISPLAY_DEPENDENCY_PROFILE_REFS = (
    "opl:runtime-env:prepare",
    "opl:scholarskills.display:dependency-profile",
    "opl:scholarskills.display:doctor",
)
SCHOLAR_DISPLAY_RUN_CONTEXT_REFS = (
    "opl:run-context:prepared-runtime-env",
    "opl:scholarskills.display:run-context",
    "opl:scholarskills.display:render-cache",
)
SCHOLAR_DISPLAY_ARTIFACT_REFS = (
    "display_pack_agent_orchestration",
    "paper/build/display_pack_lock.json",
    "paper/figure_render_receipt.json",
    "paper/figure_visual_audit_receipt.json",
    "display_pack_gallery_manifest",
)
SCHOLAR_DISPLAY_EXECUTION_RECEIPT_EXPECTATION = {
    "surface_kind": "mas_scholar_display_execution_receipt_expectation",
    "schema_version": 1,
    "module_id": SCHOLAR_DISPLAY_MODULE_ID,
    "receipt_owner": "one-person-lab",
    "receipt_role": "candidate_display_execution_receipt",
    "required_ref_families": [
        "input_fingerprint_ref",
        "dependency_profile_ref",
        "prepared_run_context_ref",
        "render_cache_ref",
        "artifact_manifest_ref",
        "visual_audit_or_gallery_preview_ref",
    ],
    "mas_owner_receipt_required_for_paper_truth": True,
    "execution_receipt_can_authorize_publication_readiness": False,
}
SCHOLAR_DISPLAY_OWNER_CONSUMPTION_BOUNDARY = {
    "surface_kind": "mas_scholar_display_owner_consumption_boundary",
    "schema_version": 1,
    "candidate_output_only": True,
    "owner_consumption_evidence": "refs_only",
    "counts_as_paper_truth": False,
    "counts_as_current_package_authority": False,
    "counts_as_owner_receipt": False,
    "mas_owner_gate_required_for_paper_truth": True,
}
SCHOLAR_DISPLAY_EXECUTION_RECEIPT_REF_ALIASES = {
    "input_fingerprint_ref": (
        "input_fingerprint_ref",
        "source_input_fingerprint_ref",
    ),
    "dependency_profile_ref": (
        "dependency_profile_ref",
        "dependency_prepared_receipt_ref",
        "dependency_receipt_ref",
    ),
    "prepared_run_context_ref": (
        "prepared_run_context_ref",
        "run_context_ref",
        "prepared_runtime_env_ref",
    ),
    "render_cache_ref": (
        "render_cache_ref",
        "display_render_cache_ref",
    ),
    "artifact_manifest_ref": (
        "artifact_manifest_ref",
        "display_artifact_manifest_ref",
    ),
    "visual_audit_or_gallery_preview_ref": (
        "visual_audit_or_gallery_preview_ref",
        "visual_audit_ref",
        "gallery_preview_ref",
    ),
}
COMMON_SCHOLARSKILLS_EXECUTION_RECEIPT_REF_ALIASES = {
    "input_fingerprint_ref": (
        "input_fingerprint_ref",
        "source_input_fingerprint_ref",
    ),
    "dependency_profile_ref": (
        "dependency_profile_ref",
        "dependency_prepared_receipt_ref",
        "dependency_receipt_ref",
    ),
    "prepared_run_context_ref": (
        "prepared_run_context_ref",
        "run_context_ref",
        "prepared_runtime_env_ref",
    ),
    "artifact_manifest_ref": (
        "artifact_manifest_ref",
        "output_artifact_manifest_ref",
        "candidate_artifact_manifest_ref",
    ),
}


def scholarskills_module_metadata(
    *, display_trigger_terms: Iterable[str] = ()
) -> dict[str, dict[str, Any]]:
    return {
        "display": {
            "capability_family": "scholarskills_display",
            "source_frameworks": [
                "MAS Scholar Skills",
                "Scholar Display",
                "MAS Display Pack",
            ],
            "action_triggers": [
                "display_pack_orchestrate",
                "display_pack_figure_plan",
                "display_pack_preflight",
                "display_pack_render",
                "artifact_display_surface_materialization_required",
            ],
            "current_delta_trigger_terms": [
                *list(display_trigger_terms),
                "scholarskills",
                "scholar display",
                "publication display",
                "display pack",
                "gallery preview",
            ],
            "current_delta_trigger_reason": "current_delta_declared_scholar_display_need",
            "descriptor_refs": list(SCHOLAR_DISPLAY_DESCRIPTOR_REFS),
            "dependency_profile_refs": list(SCHOLAR_DISPLAY_DEPENDENCY_PROFILE_REFS),
            "run_context_refs": list(SCHOLAR_DISPLAY_RUN_CONTEXT_REFS),
            "artifact_refs": list(SCHOLAR_DISPLAY_ARTIFACT_REFS),
            "required_ref_families": list(
                SCHOLAR_DISPLAY_EXECUTION_RECEIPT_EXPECTATION["required_ref_families"]
            ),
            "bridged_capability_refs": [
                "scientific-capability:display_pack_visual_capability",
                "display-pack-contract.v2",
            ],
            "role": (
                "scholarskills_display_descriptor_bridge_to_mas_display_pack_candidate_"
                "artifact_refs_without_paper_truth_authority"
            ),
        },
        "tables": {
            "capability_family": "scholarskills_tables",
            "source_frameworks": [
                "MAS Scholar Skills",
                "Scholar Tables",
                "Tables / Reporting",
            ],
            "action_triggers": [
                "table_reporting_materialization_required",
                "prepare_table_package",
                "reporting_guideline_check",
            ],
            "current_delta_trigger_terms": [
                "tables",
                "table 1",
                "model performance table",
                "supplementary table",
                "reporting guideline",
                "journal table style",
                "table_manifest_ref",
            ],
            "current_delta_trigger_reason": "current_delta_declared_scholar_tables_need",
            "artifact_refs": [
                "opl:scholarskills.tables:table_manifest",
                "opl:scholarskills.tables:table_qc",
            ],
            "required_ref_families": [
                "input_fingerprint_ref",
                "dependency_profile_ref",
                "prepared_run_context_ref",
                "table_manifest_ref",
                "table_qc_ref",
            ],
            "role": "table_one_model_performance_supplement_and_reporting_refs_only_candidate",
        },
        "stats": {
            "capability_family": "scholarskills_stats",
            "source_frameworks": [
                "MAS Scholar Skills",
                "Scholar Stats",
                "Biostatistics / Clinical Analysis",
            ],
            "action_triggers": [
                "clinical_analysis_required",
                "run_biostatistics_analysis",
                "analysis_campaign_closeout",
            ],
            "current_delta_trigger_terms": [
                "stats",
                "biostatistics",
                "clinical analysis",
                "survival analysis",
                "regression",
                "calibration",
                "roc",
                "dca",
                "subgroup",
                "sensitivity analysis",
                "analysis_manifest_ref",
            ],
            "current_delta_trigger_reason": "current_delta_declared_scholar_stats_need",
            "artifact_refs": [
                "opl:scholarskills.stats:analysis_manifest",
                "opl:scholarskills.stats:reproducibility_check",
            ],
            "required_ref_families": [
                "input_fingerprint_ref",
                "dependency_profile_ref",
                "prepared_run_context_ref",
                "analysis_manifest_ref",
                "reproducibility_check_ref",
            ],
            "role": "clinical_analysis_result_manifest_and_reproducibility_refs_only_candidate",
        },
        "lit": {
            "capability_family": "scholarskills_lit",
            "source_frameworks": [
                "MAS Scholar Skills",
                "Scholar Literature",
                "Literature Management",
            ],
            "action_triggers": [
                "literature_evidence_map_required",
                "claim_citation_support_required",
                "related_work_briefing",
            ],
            "current_delta_trigger_terms": [
                "lit",
                "literature",
                "search",
                "screening",
                "citation library",
                "evidence summary",
                "claim support map",
                "related-work",
                "related work",
                "literature_evidence_map_ref",
            ],
            "current_delta_trigger_reason": "current_delta_declared_scholar_lit_need",
            "artifact_refs": [
                "opl:scholarskills.lit:evidence_map",
                "opl:scholarskills.lit:citation_manifest",
            ],
            "required_ref_families": [
                "input_fingerprint_ref",
                "dependency_profile_ref",
                "prepared_run_context_ref",
                "evidence_map_ref",
                "citation_manifest_ref",
            ],
            "role": "literature_search_screening_citation_and_claim_support_refs_only_candidate",
        },
        "write": {
            "capability_family": "scholarskills_write",
            "source_frameworks": [
                "MAS Scholar Skills",
                "Scholar Write",
                "Manuscript Writing",
            ],
            "action_triggers": [
                "draft_manuscript_section",
                "rewrite_manuscript_section",
                "response_to_reviewer_draft",
            ],
            "current_delta_trigger_terms": [
                "write",
                "manuscript writing",
                "structured writing",
                "section rewrite",
                "journal voice",
                "response-to-reviewer",
                "response to reviewer",
                "claim tightening",
                "draft_section_manifest_ref",
            ],
            "current_delta_trigger_reason": "current_delta_declared_scholar_write_need",
            "artifact_refs": [
                "opl:scholarskills.write:draft_section_manifest",
                "opl:scholarskills.write:source_trace",
            ],
            "required_ref_families": [
                "input_fingerprint_ref",
                "dependency_profile_ref",
                "prepared_run_context_ref",
                "draft_section_manifest_ref",
                "source_trace_ref",
            ],
            "role": "manuscript_section_rewrite_voice_and_claim_tightening_refs_only_candidate",
        },
        "review": {
            "capability_family": "scholarskills_review",
            "source_frameworks": [
                "MAS Scholar Skills",
                "Scholar Review",
                "Quality Review / AI Reviewer",
            ],
            "action_triggers": [
                "return_to_ai_reviewer_workflow",
                "run_quality_repair_batch",
                "publishability_audit_required",
            ],
            "current_delta_trigger_terms": [
                "review",
                "quality review",
                "ai reviewer",
                "independent review",
                "publishability audit",
                "claim/evidence/display consistency",
                "claim evidence display consistency",
                "revision routing",
                "review_report_ref",
            ],
            "current_delta_trigger_reason": "current_delta_declared_scholar_review_need",
            "artifact_refs": [
                "opl:scholarskills.review:reviewer_report",
                "opl:scholarskills.review:route_back",
            ],
            "required_ref_families": [
                "input_fingerprint_ref",
                "dependency_profile_ref",
                "prepared_run_context_ref",
                "reviewer_report_ref",
                "route_back_ref",
            ],
            "role": "independent_publishability_consistency_and_revision_route_refs_only_candidate",
        },
        "submit": {
            "capability_family": "scholarskills_submit",
            "source_frameworks": [
                "MAS Scholar Skills",
                "Scholar Submit",
                "Submission Packaging",
            ],
            "action_triggers": [
                "submission_package_required",
                "prepare_submission_package",
                "submission_readiness_packaging",
            ],
            "current_delta_trigger_terms": [
                "submit",
                "submission",
                "submission packaging",
                "journal format",
                "cover letter",
                "highlight",
                "graphical abstract",
                "supplement",
                "export package",
                "submission_package_manifest_ref",
            ],
            "current_delta_trigger_reason": "current_delta_declared_scholar_submit_need",
            "artifact_refs": [
                "opl:scholarskills.submit:package_manifest",
                "opl:scholarskills.submit:submission_checklist",
            ],
            "required_ref_families": [
                "input_fingerprint_ref",
                "dependency_profile_ref",
                "prepared_run_context_ref",
                "package_manifest_ref",
                "submission_checklist_ref",
            ],
            "role": "journal_format_cover_letter_supplement_and_export_refs_only_candidate",
        },
        "data": {
            "capability_family": "scholarskills_data",
            "source_frameworks": [
                "MAS Scholar Skills",
                "Medical Data Governance",
                "Clinical Data Governance",
            ],
            "action_triggers": [
                "source_readiness_required",
                "data_lineage_required",
                "data_manifest_release",
                "clinical_data_governance_required",
                "data_asset_version_impact_review",
            ],
            "current_delta_trigger_terms": [
                "data",
                "medical data governance",
                "clinical data governance",
                "data asset release",
                "manifest",
                "schema",
                "lineage",
                "de-identification",
                "deidentification",
                "source readiness",
                "data dictionary",
                "codebook",
                "derived variable",
                "study binding",
                "privacy tier",
                "access tier",
                "retention guardrail",
                "data_lineage_manifest_ref",
            ],
            "current_delta_trigger_reason": "current_delta_declared_scholar_data_need",
            "artifact_refs": [
                "opl:scholarskills.data:data_asset_manifest",
                "opl:scholarskills.data:dataset_manifest",
                "opl:scholarskills.data:data_dictionary",
                "opl:scholarskills.data:version_diff_impact",
                "opl:scholarskills.data:lifecycle_catalog",
                "opl:scholarskills.data:owner_gate_handoff",
                "mas-scholar-skills:medical-data-governance",
            ],
            "required_ref_families": [
                "input_fingerprint_ref",
                "dependency_profile_ref",
                "prepared_run_context_ref",
                "data_asset_manifest_ref",
                "dataset_manifest_ref",
                "data_dictionary_ref",
                "codebook_ref",
                "cleaning_normalization_readiness_ref",
                "derived_variable_registry_ref",
                "source_lineage_ref",
                "source_readiness_receipt_ref",
                "cohort_definition_lock_ref",
                "version_diff_impact_ref",
                "study_binding_ref",
                "privacy_access_tier_ref",
                "retention_guardrail_ref",
                "storage_tier_ref",
                "lifecycle_catalog_ref",
                "owner_gate_handoff_ref",
            ],
            "role": "medical_data_governance_manifest_dictionary_lineage_version_study_binding_and_lifecycle_refs_only_candidate",
        },
    }


def build_scholarskills_capabilities(
    *,
    schema_version: int,
    default_trigger: str,
    authority_boundary: Mapping[str, Any],
    display_trigger_terms: Iterable[str] = (),
) -> list[dict[str, Any]]:
    capabilities: list[dict[str, Any]] = []
    metadata_by_module = scholarskills_module_metadata(
        display_trigger_terms=display_trigger_terms
    )
    for module_name in SCHOLARSKILLS_MODULE_NAMES:
        metadata = metadata_by_module[module_name]
        module_id = f"opl.scholarskills.{module_name}"
        descriptor_refs = _dedupe_texts(
            [
                "contracts/opl-framework/scholar-skills-capability-modules.json",
                f"contracts/opl-framework/scholar-skills-capability-modules.json#modules.{module_id}",
                SCHOLARSKILLS_OPERATING_MODEL_REF,
                SCHOLARSKILLS_LOCAL_INSTALL_READBACK_REF,
                *list(metadata.get("descriptor_refs") or []),
            ]
        )
        dependency_profile_refs = list(
            metadata.get("dependency_profile_refs")
            or [
                "opl:runtime-env:prepare",
                f"opl:scholarskills.{module_name}:dependency-profile",
                f"opl:scholarskills.{module_name}:doctor",
            ]
        )
        run_context_refs = list(
            metadata.get("run_context_refs")
            or [
                "opl:run-context:prepared-runtime-env",
                f"opl:scholarskills.{module_name}:run-context",
            ]
        )
        artifact_refs = list(metadata.get("artifact_refs") or [])
        required_ref_families = list(metadata.get("required_ref_families") or [])
        execution_receipt_expectation = {
            "surface_kind": "mas_scholarskills_execution_receipt_expectation",
            "schema_version": schema_version,
            "module_id": module_id,
            "receipt_owner": "one-person-lab",
            "receipt_role": "candidate_scholarskills_execution_receipt",
            "required_ref_families": required_ref_families,
            "mas_owner_receipt_required_for_paper_truth": True,
            "execution_receipt_can_authorize_publication_readiness": False,
        }
        if module_id == SCHOLAR_DISPLAY_MODULE_ID:
            execution_receipt_expectation = dict(
                SCHOLAR_DISPLAY_EXECUTION_RECEIPT_EXPECTATION
            )
            execution_receipt_expectation["schema_version"] = schema_version
        owner_consumption_boundary = {
            "surface_kind": "mas_scholarskills_owner_consumption_boundary",
            "schema_version": schema_version,
            "module_id": module_id,
            "candidate_output_only": True,
            "owner_consumption_evidence": "refs_only",
            "counts_as_paper_truth": False,
            "counts_as_current_package_authority": False,
            "counts_as_owner_receipt": False,
            "mas_owner_gate_required_for_paper_truth": True,
            "owner_gated_refs_consumption": True,
        }
        if module_id == SCHOLAR_DISPLAY_MODULE_ID:
            owner_consumption_boundary = dict(SCHOLAR_DISPLAY_OWNER_CONSUMPTION_BOUNDARY)
            owner_consumption_boundary["schema_version"] = schema_version
        capabilities.append(
            _capability_payload(
                capability_id=module_id,
                capability_family=_require_text(
                    metadata.get("capability_family"),
                    f"{module_id}.capability_family",
                ),
                module_id=module_id,
                source_frameworks=_dedupe_texts(
                    [
                        SCHOLARSKILLS_SOURCE_REPO_REF,
                        *list(metadata.get("source_frameworks") or []),
                    ]
                ),
                action_triggers=list(metadata.get("action_triggers") or []),
                current_delta_trigger_terms=list(
                    metadata.get("current_delta_trigger_terms") or []
                ),
                current_delta_trigger_reason=_text(
                    metadata.get("current_delta_trigger_reason")
                )
                or None,
                default_trigger=default_trigger,
                authority_boundary=authority_boundary,
                invocation_kind="descriptor_only_current_owner_input_refs",
                callable_surface=f"descriptor_only:{module_id}",
                output_refs=artifact_refs,
                contract_refs=descriptor_refs,
                descriptor_refs=descriptor_refs,
                dependency_profile_refs=dependency_profile_refs,
                run_context_refs=run_context_refs,
                artifact_refs=artifact_refs,
                execution_receipt_expectation=execution_receipt_expectation,
                owner_consumption_boundary=owner_consumption_boundary,
                externalization_guard=_non_display_migration_guard(module_name),
                bridged_capability_refs=list(
                    metadata.get("bridged_capability_refs") or []
                ),
                module_classification=_module_classification(module_name),
                role=_require_text(metadata.get("role"), f"{module_id}.role"),
            )
        )
    return capabilities


def scholarskills_execution_receipt_ref_aliases(
    *,
    capability_id: str,
    required_ref_families: Iterable[str],
) -> dict[str, tuple[str, ...]]:
    if capability_id == SCHOLAR_DISPLAY_MODULE_ID:
        return dict(SCHOLAR_DISPLAY_EXECUTION_RECEIPT_REF_ALIASES)
    aliases: dict[str, tuple[str, ...]] = {}
    for family in required_ref_families:
        base_aliases = COMMON_SCHOLARSKILLS_EXECUTION_RECEIPT_REF_ALIASES.get(family)
        aliases[family] = tuple(base_aliases or (family,))
    return aliases


def _capability_payload(
    *,
    capability_id: str,
    capability_family: str,
    module_id: str,
    source_frameworks: list[str],
    action_triggers: list[str],
    default_trigger: str,
    authority_boundary: Mapping[str, Any],
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
    externalization_guard: Mapping[str, Any] | None = None,
    bridged_capability_refs: list[str] | None = None,
    module_classification: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "capability_id": capability_id,
        "capability_family": capability_family,
        "source_repo_ref": SCHOLARSKILLS_SOURCE_REPO_REF,
        "source_frameworks": source_frameworks,
        "trigger": default_trigger,
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
        "authority_boundary": dict(authority_boundary),
        "module_id": module_id,
        "local_install": {
            "source_repo_ref": SCHOLARSKILLS_SOURCE_REPO_REF,
            "install_owner": "one-person-lab",
            "install_scopes": ["workspace", "quest"],
            "workspace": build_scholarskills_local_install_template()["workspace"],
            "quest": build_scholarskills_local_install_template()["quest"],
            "mas_program_repo_mirror_path": SCHOLARSKILLS_MAS_PROGRAM_REPO_MIRROR_PATH,
            "mas_program_repo_plugin_is_execution_source": False,
            "owner_gated_refs_consumption": True,
        },
    }
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
    if externalization_guard:
        payload["externalization_guard"] = dict(externalization_guard)
    if bridged_capability_refs:
        payload["bridged_capability_refs"] = list(bridged_capability_refs)
    if module_classification:
        payload["module_classification"] = dict(module_classification)
    payload["descriptor_only"] = True
    payload["external_runner_invocation_allowed"] = False
    return payload


def _non_display_migration_guard(module_name: str) -> dict[str, Any]:
    audit = SCHOLARSKILLS_NON_DISPLAY_MIGRATION_AUDIT.get(module_name)
    if not audit:
        return {}
    classification = _module_classification(module_name)
    return {
        "surface_kind": "mas_scholarskills_non_display_migration_guard",
        "schema_version": 1,
        "module_name": module_name,
        "migration_target": "mas-scholar-skills",
        "migration_priority": audit["migration_priority"],
        "module_classification": classification["classification"],
        "specialist_skill_id": classification.get("specialist_skill_id"),
        "contract_layer_module": bool(classification["contract_layer_module"]),
        "source_of_truth_repo": SCHOLARSKILLS_SOURCE_REPO_REF,
        "mas_role": "refs_only_descriptor_and_owner_gate_consumer",
        "mas_module_authority_owner": False,
        "mas_second_truth_allowed": False,
        "mas_may_write_scholarskills_authority": False,
        "mas_retained_authority": list(audit["mas_retained_authority"]),
    }


def _module_classification(module_name: str) -> dict[str, Any]:
    specialist_skill_id = SCHOLARSKILLS_REAL_SKILL_BACKED_MODULES.get(module_name)
    return {
        "surface_kind": "mas_scholarskills_module_classification",
        "schema_version": 1,
        "module_name": module_name,
        "classification": (
            "real_specialist_skill_backed_module"
            if specialist_skill_id
            else "unsupported_or_deferred_module_without_active_specialist_skill"
        ),
        "specialist_skill_id": specialist_skill_id,
        "contract_layer_module": False,
        "codex_discovery_sync_required": bool(specialist_skill_id),
        "source_policy": (
            "real_skill_source_in_external_mas_scholar_skills_repo"
            if specialist_skill_id
            else "not_active_in_mas_scholar_skills"
        ),
        "promotion_policy": "add_active_professional_skill_only_when_stable_MAS_specialist_workflow_exists",
        "mas_private_implementation": False,
        "stage_prompt_source": False,
        "authority_owner": False,
    }


def _dedupe_texts(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _merge_mappings(*values: object) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for value in values:
        result.update(_mapping(value))
    return result


def _text_list(value: object) -> list[str]:
    if isinstance(value, (str, Path)):
        text = _text(value)
        return [text] if text else []
    if not isinstance(value, (list, tuple, set)):
        return []
    return [text for item in value if (text := _text(item))]


def _require_text(value: Any, field: str) -> str:
    text = _text(value)
    if not text:
        raise ValueError(f"missing required ScholarSkills field: {field}")
    return text


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()
