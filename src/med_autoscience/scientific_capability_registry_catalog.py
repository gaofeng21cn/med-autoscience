from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience import external_learning_adoption_closure
from med_autoscience.scholarskills_capability_modules import (
    build_scholarskills_capabilities,
)
from med_autoscience.scientific_capability_registry.registry_contract import (
    authority_boundary as _authority_boundary,
)

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
            capability_id="evo_scientist_progress_patterns",
            capability_family="progress_accelerator",
            source_frameworks=["EvoScientist", "EvoSkills"],
            action_triggers=["*"],
            invocation_kind="descriptor_only_current_owner_input_refs",
            callable_surface="descriptor_only:opl_capability_registry_external_learning_refs",
            output_refs=["contracts/evo_scientist_progress_accelerator.json"],
            role="external_pattern_provenance_and_domain_boundary_refs",
            contract_refs=["contracts/evo_scientist_progress_accelerator.json"],
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
            role="hypothesis_portfolio_tournament_strategy_retrospective_refs_only_affordance",
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
                "readback:opl_packages_status_mas#dependency_readiness/mas-scholar-skills",
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
            capability_id="reviewer_revision_feedbackops_oma_work_order",
            capability_family="feedbackops_oma_work_order",
            source_frameworks=[
                "MAS reviewer_revision intake",
                "OPL FeedbackOps",
                "OPL Agent Lab",
                "OPL Meta Agent / OMA",
                "MAS Scholar Skills",
            ],
            action_triggers=[
                "reviewer_revision",
                "return_to_ai_reviewer_workflow",
                "run_quality_repair_batch",
            ],
            current_delta_trigger_terms=[
                "reviewer_revision",
                "major revision",
                "大修改",
                "coverage audit",
                "FeedbackOps",
                "OMA",
            ],
            current_delta_trigger_reason="current_delta_declared_reviewer_revision_feedbackops_or_oma_need",
            invocation_kind="mas_domain_feedbackops_dispatch_request",
            callable_surface=(
                "med_autoscience.reviewer_revision_feedbackops_dispatch:"
                "build_reviewer_revision_feedbackops_dispatch_request"
            ),
            output_refs=[
                "artifacts/agent_lab/medical_manuscript_quality/latest_suite.json",
                "artifacts/agent_lab/medical_manuscript_quality/feedbackops_dispatch_request.json",
                "artifacts/agent_lab/medical_manuscript_quality/feedbackops_execution_readback.json",
                "candidate:developer_patch_work_order_ref",
                "candidate:reviewer_revision_coverage_audit_ref",
                "candidate:stage_attempt_readback_ref",
            ],
            contract_refs=[
                "docs/decisions.md#2026-07-02reviewer-revision-质量反馈默认触发-opl-agent-lab--oma-自进化",
                "contracts/mas-paper-study-stage-pack.json#/reviewer_revision_default_mechanism",
                "src/med_autoscience/study_task_intake_revision.py",
                "src/med_autoscience/reviewer_revision_feedbackops_dispatch.py",
            ],
            role=(
                "reviewer_revision_feedbackops_dispatch_oma_work_order_and_"
                "coverage_audit_readback_refs_only_cli_dispatch"
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
