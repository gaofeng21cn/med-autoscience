from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


SCHOLAR_DISPLAY_MODULE_ID = "opl.scholarskills.display"
SCHOLARSKILLS_MODULE_NAMES = (
    "display",
    "tables",
    "stats",
    "omics",
    "lit",
    "write",
    "review",
    "submit",
    "data",
    "intake",
)
SCHOLARSKILLS_CAPABILITY_IDS = tuple(
    f"opl.scholarskills.{name}" for name in SCHOLARSKILLS_MODULE_NAMES
)
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
                "OPL ScholarSkills",
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
                "OPL ScholarSkills",
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
                "OPL ScholarSkills",
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
        "omics": {
            "capability_family": "scholarskills_omics",
            "source_frameworks": [
                "OPL ScholarSkills",
                "Scholar Omics",
                "Omics / Bioinformatics",
            ],
            "action_triggers": [
                "omics_bioinformatics_analysis_required",
                "run_omics_workflow",
                "result_to_figure_gate",
            ],
            "current_delta_trigger_terms": [
                "omics",
                "bioinformatics",
                "single-cell",
                "single cell",
                "bulk rna",
                "cnv",
                "mutation",
                "pathway",
                "enrichment",
                "dimensionality reduction",
                "marker",
                "landscape",
                "omics_workflow_manifest_ref",
            ],
            "current_delta_trigger_reason": "current_delta_declared_scholar_omics_need",
            "artifact_refs": [
                "opl:scholarskills.omics:omics_pipeline_manifest",
                "opl:scholarskills.omics:feature_matrix_qc",
            ],
            "required_ref_families": [
                "input_fingerprint_ref",
                "dependency_profile_ref",
                "prepared_run_context_ref",
                "omics_pipeline_manifest_ref",
                "feature_matrix_qc_ref",
            ],
            "role": "omics_workflow_analysis_manifest_and_result_refs_only_candidate",
        },
        "lit": {
            "capability_family": "scholarskills_lit",
            "source_frameworks": [
                "OPL ScholarSkills",
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
                "OPL ScholarSkills",
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
                "OPL ScholarSkills",
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
                "OPL ScholarSkills",
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
                "OPL ScholarSkills",
                "Scholar Data",
                "Data Management",
            ],
            "action_triggers": [
                "source_readiness_required",
                "data_lineage_required",
                "data_manifest_release",
            ],
            "current_delta_trigger_terms": [
                "data",
                "data management",
                "data asset release",
                "manifest",
                "schema",
                "lineage",
                "de-identification",
                "deidentification",
                "source readiness",
                "data_lineage_manifest_ref",
            ],
            "current_delta_trigger_reason": "current_delta_declared_scholar_data_need",
            "artifact_refs": [
                "opl:scholarskills.data:data_manifest",
                "opl:scholarskills.data:lineage_readiness",
            ],
            "required_ref_families": [
                "input_fingerprint_ref",
                "dependency_profile_ref",
                "prepared_run_context_ref",
                "data_manifest_ref",
                "lineage_readiness_ref",
            ],
            "role": "data_manifest_schema_lineage_and_source_readiness_refs_only_candidate",
        },
        "intake": {
            "capability_family": "scholarskills_intake",
            "source_frameworks": [
                "OPL ScholarSkills",
                "Scholar Intake",
                "External Method Skill Intake",
            ],
            "action_triggers": [
                "external_method_skill_intake",
                "capability_adoption_contract_required",
                "external_learning_adoption",
            ],
            "current_delta_trigger_terms": [
                "intake",
                "external method",
                "open-source project",
                "paper method",
                "codebase",
                "manual template",
                "adoption contract",
                "default capability",
                "intake_adoption_contract_ref",
            ],
            "current_delta_trigger_reason": "current_delta_declared_scholar_intake_need",
            "artifact_refs": [
                "opl:scholarskills.intake:source_snapshot",
                "opl:scholarskills.intake:adoption_contract",
            ],
            "required_ref_families": [
                "input_fingerprint_ref",
                "dependency_profile_ref",
                "prepared_run_context_ref",
                "source_snapshot_ref",
                "adoption_contract_ref",
            ],
            "role": "external_method_skill_adoption_contract_and_descriptor_refs_only_candidate",
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
                source_frameworks=list(metadata.get("source_frameworks") or []),
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
                bridged_capability_refs=list(
                    metadata.get("bridged_capability_refs") or []
                ),
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


def build_scholarskills_materialized_package_input(
    *,
    capability_id: str,
    required_ref_families: Iterable[str],
    execution_receipt_path: Path | str | None,
    materialized_package_manifest_path: Path | str | None,
) -> dict[str, Any]:
    manifest_path = _optional_json_path(materialized_package_manifest_path)
    receipt_path = _optional_json_path(execution_receipt_path)
    manifest: dict[str, Any] = {}
    if manifest_path:
        manifest = _read_json_mapping(
            manifest_path, label="materialized_package_manifest_path"
        )
        embedded_receipt_ref = _text(manifest.get("execution_receipt_candidate_path"))
        embedded_receipt_ref = embedded_receipt_ref or _text(
            manifest.get("execution_receipt_path")
        )
        if embedded_receipt_ref and receipt_path is None:
            receipt_path = _resolve_ref_path(
                embedded_receipt_ref, base=manifest_path.parent
            )

    receipt: dict[str, Any] = {}
    if receipt_path:
        receipt = _read_json_mapping(receipt_path, label="execution_receipt_path")
    embedded_receipt = _mapping(manifest.get("execution_receipt_candidate"))
    if embedded_receipt and not receipt:
        receipt = embedded_receipt

    observed_module_ids = _dedupe_texts(
        [
            _text(manifest.get("module_id")),
            _text(receipt.get("module_id")),
        ]
    )
    mismatched_module_ids = [
        module_id for module_id in observed_module_ids if module_id != capability_id
    ]
    if mismatched_module_ids:
        raise ValueError(
            "OPL ScholarSkills materialized package module_id mismatch: "
            + ", ".join(mismatched_module_ids)
        )

    raw_refs = _materialized_package_refs(
        required_ref_families=required_ref_families,
        manifest=manifest,
        receipt=receipt,
        manifest_path=manifest_path,
        receipt_path=receipt_path,
    )
    authority_flags = _merge_mappings(
        manifest.get("authority_flags"),
        receipt.get("authority_flags"),
    )
    authority_flags.update(_top_level_authority_claims(manifest))
    authority_flags.update(_top_level_authority_claims(receipt))
    truthy_authority_flags = [
        key for key, value in authority_flags.items() if value is True
    ]
    if truthy_authority_flags:
        raise ValueError(
            "OPL ScholarSkills materialized package authority flags must be false: "
            + ", ".join(sorted(truthy_authority_flags))
        )
    written_files = _dedupe_texts(
        [
            *_text_list(manifest.get("written_files")),
            *_text_list(receipt.get("written_files")),
        ]
    )
    forbidden_collisions = _forbidden_materialized_package_written_refs(written_files)
    if forbidden_collisions:
        raise ValueError(
            "OPL ScholarSkills materialized package reports forbidden authority writes: "
            + ", ".join(forbidden_collisions)
        )
    if not (manifest or receipt or raw_refs):
        return {}
    return {
        "execution_receipt": receipt,
        "execution_receipt_refs": raw_refs,
        "materialized_package_consumption": {
            "surface_kind": "mas_scholarskills_materialized_package_consumption",
            "schema_version": 1,
            "refs_only": True,
            "manifest_path": str(manifest_path) if manifest_path else None,
            "execution_receipt_path": str(receipt_path) if receipt_path else None,
            "module_id": _text(receipt.get("module_id"))
            or _text(manifest.get("module_id"))
            or capability_id,
            "sha256": _text(receipt.get("sha256"))
            or _text(manifest.get("sha256"))
            or None,
            "authority_flags": {
                key: value
                for key, value in authority_flags.items()
                if isinstance(value, bool)
            },
            "authority_flags_false": not truthy_authority_flags,
            "written_files": written_files,
            "forbidden_written_file_collisions": forbidden_collisions,
            "mas_consumer_written_files": [],
            "counts_as_paper_truth": False,
            "counts_as_owner_receipt": False,
            "can_authorize_publication_readiness": False,
            "can_write_publication_eval": False,
            "can_write_controller_decisions": False,
            "can_write_current_package": False,
            "can_write_paper_or_package": False,
            "can_write_study_truth": False,
            "can_write_typed_blocker": False,
            "can_write_human_gate": False,
        },
    }


def _materialized_package_refs(
    *,
    required_ref_families: Iterable[str],
    manifest: Mapping[str, Any],
    receipt: Mapping[str, Any],
    manifest_path: Path | None,
    receipt_path: Path | None,
) -> dict[str, str]:
    refs: dict[str, str] = {}
    if receipt_path:
        refs["execution_receipt_ref"] = str(receipt_path)
    elif manifest_path:
        refs["execution_receipt_ref"] = str(manifest_path)
    execution_receipt_ref = _text(receipt.get("execution_receipt_ref"))
    execution_receipt_ref = execution_receipt_ref or _text(
        manifest.get("execution_receipt_ref")
    )
    if execution_receipt_ref:
        refs["execution_receipt_ref"] = execution_receipt_ref
    for payload in (manifest, receipt):
        refs.update(_mapping(payload.get("execution_receipt_refs")))
        refs.update(_mapping(payload.get("refs")))
        artifact_manifest_path = _text(payload.get("artifact_manifest_path"))
        if artifact_manifest_path and "artifact_manifest_ref" not in refs:
            refs["artifact_manifest_ref"] = artifact_manifest_path
            refs.setdefault(
                _module_manifest_family(required_ref_families),
                artifact_manifest_path,
            )
    return {key: value for key, value in refs.items() if _text(value)}


def _module_manifest_family(required_ref_families: Iterable[str]) -> str:
    for family in _text_list(list(required_ref_families)):
        if family.endswith("_manifest_ref"):
            return family
    return "artifact_manifest_ref"


def _optional_json_path(value: Path | str | None) -> Path | None:
    text = _text(value)
    return Path(text).expanduser().resolve() if text else None


def _resolve_ref_path(value: str, *, base: Path) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def _read_json_mapping(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"{label} does not exist: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} is not valid JSON: {path}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError(f"{label} must contain a JSON object: {path}")
    return dict(payload)


def _forbidden_materialized_package_written_refs(values: list[str]) -> list[str]:
    forbidden: list[str] = []
    for value in values:
        normalized = value.replace("\\", "/")
        if (
            normalized.endswith("/artifacts/publication_eval/latest.json")
            or normalized == "artifacts/publication_eval/latest.json"
            or normalized.endswith("/artifacts/controller_decisions/latest.json")
            or normalized == "artifacts/controller_decisions/latest.json"
            or "/current_package/" in normalized
            or normalized.endswith("/current_package")
            or "/typed_blocker" in normalized
            or "/human_gate" in normalized
            or "/owner_receipt" in normalized
        ):
            forbidden.append(value)
    return forbidden


def _top_level_authority_claims(payload: Mapping[str, Any]) -> dict[str, bool]:
    authority_keys = (
        "counts_as_paper_truth",
        "counts_as_owner_receipt",
        "can_authorize_publication_readiness",
        "can_claim_domain_ready",
        "can_claim_quality_verdict",
        "can_claim_artifact_authority",
        "can_claim_production_ready",
        "can_claim_runtime_ready",
        "can_schedule_runtime",
        "can_write_domain_truth",
        "can_write_runtime_state",
        "can_write_memory_body",
        "can_mutate_artifact_body",
        "can_sign_owner_receipt",
        "can_create_typed_blocker",
        "can_write_publication_eval",
        "can_write_controller_decisions",
        "can_write_current_package",
        "can_write_paper_or_package",
        "can_write_study_truth",
        "can_write_owner_receipt",
        "can_write_typed_blocker",
        "can_write_human_gate",
    )
    return {
        key: value
        for key in authority_keys
        if isinstance((value := payload.get(key)), bool)
    }


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
    bridged_capability_refs: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "capability_id": capability_id,
        "capability_family": capability_family,
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
    if bridged_capability_refs:
        payload["bridged_capability_refs"] = list(bridged_capability_refs)
    payload["descriptor_only"] = True
    payload["external_runner_invocation_allowed"] = False
    return payload


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
