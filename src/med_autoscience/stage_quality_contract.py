from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from med_autoscience.stage_quality_contract_parts.pack_data import (
    _JOURNAL_ACCEPTANCE_EVIDENCE_FIELDS,
    _JOURNAL_EXTENSION_CONTRACTS,
    _JOURNAL_FAMILY_PATTERNS,
    _JOURNAL_REQUIRED_REVIEWER_OUTPUTS,
    _PACK_OWNER_REFS,
    _PACK_REQUIRED_REFS,
    _PACK_TITLES,
    _REVIEWER_PRECOMMITMENT_PACK_IDS,
)
from med_autoscience.stage_quality_contract_parts.pack_applicability import (
    _PACK_STAGE_MAP,
    _PACK_STUDY_ARCHETYPE_MAP,
)
from med_autoscience.stage_quality_contract_parts.data_access import (
    build_data_access_ground_truth_isolation,
    data_access_level_ids,
)
from med_autoscience.stage_quality_contract_parts.journal_currentness import (
    JOURNAL_POLICY_CURRENTNESS_PACKS,
    LITERATURE_SEARCH_SOURCE_PACKS,
    build_citation_verification_pack,
    build_journal_policy_currentness_pack,
    build_literature_search_source_pack,
    build_source_citation_authority_pack,
)
from med_autoscience.stage_quality_contract_parts.life_science_source_discovery import (
    LIFE_SCIENCE_SOURCE_DISCOVERY_PACK_ID,
    build_life_science_clean_room_absorption,
    build_life_science_source_discovery_pack,
)
from med_autoscience.stage_quality_contract_parts.autosci_research_lifecycle import (
    AUTOSCI_RESEARCH_LIFECYCLE_PACKS,
    build_autosci_clean_room_absorption,
    build_autosci_pack_contracts,
)
from med_autoscience.stage_quality_contract_parts.light_external import (
    LIGHT_MATERIALIZER_OUTPUT_REF_KINDS,
    LIGHT_OBSERVED_HEAD,
    build_light_materializer_contract,
)
from med_autoscience.stage_quality_contract_parts.maturity import (
    PACK_MATURITY_STATUS,
    STRONG_PROMOTION_EVIDENCE_KINDS,
    build_promotion_evidence,
)


SURFACE_KIND = "mas_stage_quality_pack_contract"
VERSION = "mas-stage-quality-pack-contract.v1"
PROJECTION_KIND = "stage_quality_pack_projection"
CONTRACT_REF = "med_autoscience.stage_quality_contract.build_stage_quality_pack_contract"
REPO_PATH = "src/med_autoscience/stage_quality_contract.py"

PACK_ROLE = "quality_input_and_reviewer_rubric"
REFRESH_POLICY = "rebuild_product_entry_manifest_before_opl_discovery"

REQUIRED_STAGE_QUALITY_PACK_IDS: tuple[str, ...] = (
    "ai_native_expert_judgment_pack",
    "medical_claim_evidence_pack",
    "statistical_analysis_pack",
    "reporting_guideline_pack",
    "manuscript_argument_pack",
    "statistical_reporting_pack",
    "display_to_claim_pack",
    "journal_response_pack",
    "data_availability_fair_pack",
    "citation_integrity_pack",
    "figure_evidence_contract_pack",
    "paper_reader_grounding_pack",
    "paper_presentation_pack",
    LIFE_SCIENCE_SOURCE_DISCOVERY_PACK_ID,
    "route_memory_pack",
    "stop_loss_pack",
    "external_pattern_intake_pack",
    "artifact_freshness_pack",
    "human_gate_pack",
)

JOURNAL_FAMILY_QUALITY_PACK_IDS: tuple[str, ...] = (
    "journal_response_pack",
    "data_availability_fair_pack",
    "citation_integrity_pack",
    "figure_evidence_contract_pack",
    "manuscript_argument_pack",
    "paper_reader_grounding_pack",
    "paper_presentation_pack",
    "statistical_reporting_pack",
)

QUALITY_PACK_CONTRACT_SURFACES: tuple[str, ...] = (SURFACE_KIND, PROJECTION_KIND)
CLINICAL_BASE_GUIDELINES: tuple[str, ...] = (
    "STROBE",
    "TRIPOD",
    "TRIPOD-AI",
    "CONSORT",
    "PRISMA",
    "STARD",
    "CARE",
)

def build_stage_quality_pack_contract() -> dict[str, Any]:
    packs = [_build_pack(pack_id) for pack_id in REQUIRED_STAGE_QUALITY_PACK_IDS]
    return {
        "surface_kind": SURFACE_KIND,
        "version": VERSION,
        "owner": "MedAutoScience",
        "contract_ref": CONTRACT_REF,
        "repo_source_ref": REPO_PATH,
        "pack_ids": list(REQUIRED_STAGE_QUALITY_PACK_IDS),
        "packs": packs,
        "pack_locators": {
            pack["pack_id"]: {
                "ref_kind": "json_pointer",
                "ref": f"/product_entry_manifest/stage_quality_pack_contract/packs/{pack['pack_id']}",
                "role": "quality_pack_descriptor",
            }
            for pack in packs
        },
        "freshness": {
            "freshness_kind": "product_entry_manifest_projection",
            "refresh_policy": REFRESH_POLICY,
            "source_ref": REPO_PATH,
            "stale_if_contract_source_missing": True,
        },
        "data_access_ground_truth_isolation": build_data_access_ground_truth_isolation(),
        "authority_boundary": _contract_authority_boundary(),
        "opl_projection_boundary": {
            "role": "descriptor_ref_freshness_locator_only",
            "allowed_fields": [
                "contract_ref",
                "pack_ids",
                "freshness",
                "pack_locators",
                "data_access_ground_truth_isolation",
                "authority_boundary",
            ],
            "forbidden_outputs": [
                "quality_verdict",
                "publication_readiness",
                "submission_readiness",
                "mas_truth_write",
            ],
        },
    }


def build_stage_quality_pack_projection() -> dict[str, Any]:
    return {
        "surface_kind": PROJECTION_KIND,
        "contract_ref": CONTRACT_REF,
        "pack_ids": list(REQUIRED_STAGE_QUALITY_PACK_IDS),
        "pack_count": len(REQUIRED_STAGE_QUALITY_PACK_IDS),
        "pack_role": PACK_ROLE,
        "publication_readiness_authority": False,
        "quality_verdict_authority": False,
        "freshness_ref": "/product_entry_manifest/stage_quality_pack_contract/freshness",
        "locator_ref": "/product_entry_manifest/stage_quality_pack_contract/pack_locators",
        "authority_boundary_ref": "/product_entry_manifest/stage_quality_pack_contract/authority_boundary",
        "data_access_ground_truth_isolation_ref": (
            "/product_entry_manifest/stage_quality_pack_contract/data_access_ground_truth_isolation"
        ),
        "data_access_levels": data_access_level_ids(),
        "runtime_permission_authority": False,
        "source_discovery_pack_ref": (
            "/product_entry_manifest/stage_quality_pack_contract/packs/life_science_source_discovery_pack"
        ),
        "external_source_plugin_dependency": False,
        "source_discovery_authority": False,
    }


def build_stage_quality_pack_locator_projection() -> dict[str, Any]:
    return {
        "ref_kind": "json_pointer",
        "ref": "/product_entry_manifest/stage_quality_pack_contract",
        "freshness_ref": "/product_entry_manifest/stage_quality_pack_contract/freshness",
        "locator_ref": "/product_entry_manifest/stage_quality_pack_contract/pack_locators",
        "authority_boundary_ref": "/product_entry_manifest/stage_quality_pack_contract/authority_boundary",
        "opl_projection_boundary": "descriptor_ref_freshness_locator_only",
        "can_write_mas_truth": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
    }


def quality_pack_ids_for_stages(stage_ids: Iterable[str]) -> list[str]:
    stage_set = {str(stage_id) for stage_id in stage_ids}
    selected: list[str] = []
    for pack_id in REQUIRED_STAGE_QUALITY_PACK_IDS:
        pack_stages = set(_PACK_STAGE_MAP[pack_id])
        if "human_gate_pack" == pack_id or stage_set & pack_stages:
            selected.append(pack_id)
    return selected


def build_stage_quality_pack_ref_projection(stage_ids: Iterable[str]) -> dict[str, Any]:
    return {
        "role": PACK_ROLE,
        "pack_refs": quality_pack_ids_for_stages(stage_ids),
        "contract_ref": CONTRACT_REF,
        "publication_readiness_authority": False,
        "quality_verdict_authority": False,
        "freshness_ref": "/product_entry_manifest/stage_quality_pack_contract/freshness",
        "locator_ref": "/product_entry_manifest/stage_quality_pack_contract/pack_locators",
        "authority_boundary_ref": "/product_entry_manifest/stage_quality_pack_contract/authority_boundary",
        "data_access_ground_truth_isolation_ref": (
            "/product_entry_manifest/stage_quality_pack_contract/data_access_ground_truth_isolation"
        ),
        "data_access_levels": data_access_level_ids(),
        "runtime_permission_authority": False,
        "opl_projection_boundary": "descriptor_ref_freshness_locator_only",
    }


def _build_pack(pack_id: str) -> dict[str, Any]:
    pack = {
        "pack_id": pack_id,
        "title": _PACK_TITLES[pack_id],
        "role": PACK_ROLE,
        "maturity_status": _pack_maturity_status(pack_id),
        "promotion_evidence": _pack_promotion_evidence(pack_id),
        "publication_readiness_authority": False,
        "quality_verdict_authority": False,
        "applies_to": {
            "stages": list(_PACK_STAGE_MAP[pack_id]),
            "study_archetypes": list(_PACK_STUDY_ARCHETYPE_MAP[pack_id]),
        },
        "authority_boundary": _pack_authority_boundary(),
        "owner_refs": list(_PACK_OWNER_REFS[pack_id]),
        "required_refs": list(_PACK_REQUIRED_REFS[pack_id]),
    }
    if pack_id == "reporting_guideline_pack":
        pack["guideline_selection"] = _reporting_guideline_selection()
    if pack_id in _REVIEWER_PRECOMMITMENT_PACK_IDS:
        pack["reviewer_precommitment_contract"] = _reviewer_precommitment_contract(pack_id)
    if pack_id in JOURNAL_FAMILY_QUALITY_PACK_IDS:
        pack["journal_family_patterns"] = list(_JOURNAL_FAMILY_PATTERNS[pack_id])
        pack["clean_room_absorption"] = _clean_room_absorption()
        pack["acceptance_evidence_fields"] = _journal_acceptance_evidence_fields(pack_id)
        pack["required_reviewer_output"] = _journal_required_reviewer_output(pack_id)
        pack["forbidden_authority"] = _journal_forbidden_authority()
        pack["quality_pack_consumption"] = _journal_quality_pack_consumption(pack_id)
        if pack_id in _JOURNAL_EXTENSION_CONTRACTS:
            pack["extension_contracts"] = list(_JOURNAL_EXTENSION_CONTRACTS[pack_id])
    if pack_id in LITERATURE_SEARCH_SOURCE_PACKS:
        pack["literature_search_source_pack"] = build_literature_search_source_pack()
    if pack_id in JOURNAL_POLICY_CURRENTNESS_PACKS:
        pack["journal_policy_currentness_pack"] = build_journal_policy_currentness_pack()
    if pack_id == "citation_integrity_pack":
        pack["citation_verification_pack"] = build_citation_verification_pack()
        pack["source_citation_authority_pack"] = build_source_citation_authority_pack()
    if pack_id == LIFE_SCIENCE_SOURCE_DISCOVERY_PACK_ID:
        pack["clean_room_absorption"] = build_life_science_clean_room_absorption()
        pack["life_science_source_discovery_pack"] = build_life_science_source_discovery_pack()
    if pack_id in AUTOSCI_RESEARCH_LIFECYCLE_PACKS:
        pack["autosci_clean_room_absorption"] = build_autosci_clean_room_absorption()
        pack["autosci_extension_contracts"] = build_autosci_pack_contracts(pack_id)
    if pack_id == "external_pattern_intake_pack":
        pack["clean_room_absorption"] = _light_clean_room_absorption()
        pack["pattern_adoptions"] = _light_pattern_adoptions()
        pack["materializer_contract"] = _light_materializer_contract()
        pack["forbidden_authority"] = _light_forbidden_authority()
        pack["missing_ref_policy"] = _light_missing_ref_policy()
        pack["progress_first_policy"] = _light_progress_first_policy()
        pack["skill_engineering_policy"] = _light_skill_engineering_policy()
    return pack


def _pack_maturity_status(pack_id: str) -> str:
    if pack_id == "external_pattern_intake_pack":
        return "stable_contract"
    return PACK_MATURITY_STATUS[pack_id]


def _pack_promotion_evidence(pack_id: str) -> dict[str, object]:
    if pack_id == "external_pattern_intake_pack":
        return {
            "maturity_model": "mas_contract_maturity_not_vendor_skill_status",
            "upstream_status_signal": "clean_room_pattern_source_only",
            "stable_requires_strong_evidence": True,
            "strong_evidence_kinds": list(STRONG_PROMOTION_EVIDENCE_KINDS),
            "evidence": [
                {
                    "evidence_id": "light_external_pattern_intake_contract_test",
                    "evidence_kind": "focused_tests",
                    "ref_kind": "test",
                    "ref": "tests/test_stage_quality_contract.py",
                    "role": "clean_room_non_blocking_progress_first_advisory_contract",
                    "strength": "strong",
                },
                {
                    "evidence_id": "light_external_advisory_materializer_tests",
                    "evidence_kind": "focused_tests",
                    "ref_kind": "test",
                    "ref": "tests/test_light_advisory_materializer.py",
                    "role": "mas_owned_runtime_materializer_for_advisory_refs",
                    "strength": "strong",
                },
                {
                    "evidence_id": "light_external_advisory_materializer_cli_tests",
                    "evidence_kind": "focused_tests",
                    "ref_kind": "test",
                    "ref": "tests/test_cli_cases/light_advisory_materializer_command.py",
                    "role": "operator_callable_materializer_command",
                    "strength": "strong",
                }
            ],
            "stable_strong_evidence_satisfied": True,
            "may_authorize_publication_readiness": False,
            "may_authorize_quality_verdict": False,
        }
    return build_promotion_evidence(pack_id)


def _contract_authority_boundary() -> dict[str, Any]:
    return {
        "pack_role": PACK_ROLE,
        "publication_readiness_authority": False,
        "quality_verdict_authority": False,
        "truth_owner": "MedAutoScience",
        "opl_role": "descriptor_ref_freshness_locator_consumer",
        "opl_can_write_mas_truth": False,
        "opl_can_authorize_quality_verdict": False,
        "opl_can_authorize_publication_readiness": False,
    }


def _pack_authority_boundary() -> dict[str, Any]:
    return {
        "truth_owner": "MedAutoScience",
        "quality_owner": "MedAutoScience",
        "reviewer_rubric_owner": "MedAutoScience",
        "pack_role": PACK_ROLE,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission_readiness": False,
        "can_write_domain_truth": False,
    }


def _reviewer_precommitment_contract(pack_id: str) -> dict[str, object]:
    return {
        "contract_id": f"{pack_id}.reviewer_precommitment_contract.v1",
        "source_project": "academic-research-skills",
        "absorbed_as": "mas_native_reviewer_precommitment_contract",
        "paper_blind_phase": {
            "phase_id": "paper_content_blind_precommitment",
            "allowed_inputs": ["quality_pack_descriptor", "paper_metadata_only"],
            "forbidden_inputs": [
                "paper_body",
                "manuscript_package",
                "publication_eval_verdict",
                "controller_decision_verdict",
            ],
            "expected_output_ref": "reviewer_precommitment_record",
        },
        "paper_visible_phase": {
            "phase_id": "paper_visible_review",
            "required_inputs": [
                "quality_pack_descriptor",
                "reviewer_precommitment_record",
                "verified_evidence_refs",
                "paper_or_artifact_under_review",
            ],
            "precommitment_record_must_be_reinjected": True,
            "may_rewrite_precommitment_after_viewing_paper": False,
        },
        "required_precommitment_outputs": [
            "contract_paraphrase",
            "scoring_plan",
            "contract_acknowledged_receipt",
        ],
        "required_runtime_inputs": [
            "quality_pack_descriptor",
            "paper_metadata_only",
            "reviewer_precommitment_record",
            "verified_evidence_refs",
            "paper_or_artifact_under_review",
        ],
        "separate_invocation_required": True,
        "rubric_may_authorize_quality_verdict": False,
        "rubric_may_write_truth": False,
    }


def _reporting_guideline_selection() -> list[dict[str, Any]]:
    return [
        _guideline_selection("observational_or_cohort_or_registry", ["STROBE"]),
        _guideline_selection("diagnostic_or_prognostic_model", ["TRIPOD", "TRIPOD-AI"]),
        _guideline_selection("randomized_or_intervention", ["CONSORT"]),
        _guideline_selection("systematic_review_or_meta_analysis", ["PRISMA"]),
        _guideline_selection("diagnostic_accuracy", ["STARD"]),
        _guideline_selection("case_report_or_case_series", ["CARE"]),
        _guideline_selection(
            "ai_ml_medical_study",
            ["AI/ML extension"],
            requires_clinical_base_guideline=True,
            clinical_base_guideline_options=CLINICAL_BASE_GUIDELINES,
        ),
    ]


def _guideline_selection(
    study_archetype: str,
    guideline_families: list[str],
    *,
    requires_clinical_base_guideline: bool = False,
    clinical_base_guideline_options: tuple[str, ...] = (),
) -> dict[str, Any]:
    return {
        "study_archetype": study_archetype,
        "guideline_families": list(guideline_families),
        "requires_clinical_base_guideline": requires_clinical_base_guideline,
        "clinical_base_guideline_options": list(clinical_base_guideline_options),
    }


def _clean_room_absorption() -> dict[str, object]:
    return {
        "source_project": "nature-skills",
        "absorbed_as": "mas_native_contract_pattern",
        "status_signal_consumed_as": "upstream_readme_status_only_not_mas_authority",
        "vendor_dependency": False,
        "runtime_dependency": False,
        "publication_authority": False,
        "default_skill_source": False,
    }


def _light_clean_room_absorption() -> dict[str, object]:
    return {
        "source_project": "Light0305/Light",
        "source_repository": "https://github.com/Light0305/Light",
        "observed_head": LIGHT_OBSERVED_HEAD,
        "previous_intake_head": "731c786e9434e8f6f9cd5284293003115c5b66c7",
        "source_paths": [
            "README.md",
            "CONVENTIONS.md",
            "MODE_REGISTRY.md",
            "ROUTER.md",
            "skills/light-orchestrator/SKILL.md",
            "skills/light-orchestrator/references/passport.md",
            "skills/light-orchestrator/references/checkpoints.md",
            "skills/light-orchestrator/references/pipelines.md",
            "skills/light-literature-search/SKILL.md",
            "skills/light-data-engineering/SKILL.md",
            "skills/light-research-plan/SKILL.md",
            "skills/light-result-analysis/SKILL.md",
            "skills/light-idea-generation/SKILL.md",
            "skills/light-idea-critique/SKILL.md",
            "skills/light-self-review/SKILL.md",
            "skills/light-citation/SKILL.md",
            "skills/light-citation/references/locator_audit.md",
            "skills/light-research-ethics/SKILL.md",
            "skills/light-literature-search/scripts/prisma_flow.py",
            "skills/light-figure-drawing/SKILL.md",
            "skills/light-figure-drawing/scripts/figure_export.py",
            "skills/light-figure-drawing/references/figure_integrity.md",
            "skills/light-figure-drawing/scripts/figure_integrity_lint.py",
            "skills/light-figure-planning/SKILL.md",
            "skills/light-paper-polishing/references/argument_review.md",
            "skills/light-paper-polishing/scripts/style_fingerprint.py",
            "_verification_log/*.md",
        ],
        "latest_upstream_delta": {
            "commit": LIGHT_OBSERVED_HEAD,
            "adopted_as": "figure_integrity_export_qa_advisory_pattern",
            "patterns": [
                "effective_font_size_after_scaling",
                "physical_export_size_roundtrip",
                "multi_panel_non_redundancy",
            ],
            "runtime_dependency": False,
            "hard_gate_by_default": False,
        },
        "absorbed_as": "mas_native_progress_first_advisory_and_skill_engineering_contract_pattern",
        "vendor_dependency": False,
        "runtime_dependency": False,
        "install_script_dependency": False,
        "skill_router_dependency": False,
        "orchestrator_dependency": False,
        "knowledge_base_dependency": False,
        "default_skill_source": False,
        "copy_external_runtime_or_install_scripts": False,
        "copy_external_skill_inventory": False,
    }


def _light_pattern_adoptions() -> list[dict[str, object]]:
    return [
        {
            "pattern_id": "verification_log_three_state_fresh_evidence",
            "learned_from": "_verification_log/*.md",
            "adoption_class": "adopt_contract",
            "mas_owner_surface": "quality_os_and_evidence_refs",
            "required_contract_fields": [
                "fresh_check_ref",
                "status_pass_warn_fail",
                "checked_at",
                "source_ref",
                "typed_blocker_ref_if_current_delta_requires_ref",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
        {
            "pattern_id": "core_collision_check",
            "learned_from": "skills/light-idea-generation/SKILL.md",
            "adoption_class": "adopt_contract",
            "mas_owner_surface": "idea_review_and_route_memory_refs",
            "required_contract_fields": [
                "core_claim_or_mechanism_ref",
                "nearest_neighbor_work_refs",
                "negative_search_evidence_refs",
                "novelty_delta_ref",
                "route_back_or_continue_ref",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
        {
            "pattern_id": "reviewer_refusal_rehearsal",
            "learned_from": "skills/light-idea-critique/SKILL.md",
            "adoption_class": "adopt_contract",
            "mas_owner_surface": "reviewer_os_and_decision_refs",
            "required_contract_fields": [
                "top_refusal_reason_refs",
                "reviewer_position_ref",
                "counter_evidence_or_route_back_ref",
                "unresolved_critical_ref",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
        {
            "pattern_id": "bounded_template_or_skill_card",
            "learned_from": "README.md",
            "adoption_class": "adopt_contract",
            "mas_owner_surface": "stage_quality_pack_descriptor",
            "required_contract_fields": [
                "bounded_card_id",
                "intended_stage_refs",
                "input_ref_classes",
                "output_ref_classes",
                "forbidden_authority_effects",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
        {
            "pattern_id": "self_review_evidence_gate",
            "learned_from": "skills/light-self-review/SKILL.md",
            "adoption_class": "adopt_contract",
            "mas_owner_surface": "quality_os_fresh_evidence_gate_refs",
            "required_contract_fields": [
                "claim_to_verify",
                "fresh_verification_command_or_ref",
                "verification_exit_state",
                "failure_count",
                "claim_supported",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
        {
            "pattern_id": "progress_passport_ref_ledger",
            "learned_from": "skills/light-orchestrator/references/passport.md",
            "adoption_class": "adopt_contract",
            "mas_owner_surface": "stage_attempt_ledger_and_owner_receipt_refs",
            "required_contract_fields": [
                "current_work_unit_ref",
                "stage_output_refs",
                "gate_result_refs",
                "decision_choice_ref_if_human_decision_point",
                "known_limitations_refs",
                "updated_at",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
        {
            "pattern_id": "checkpoint_gate_budget",
            "learned_from": "skills/light-orchestrator/references/checkpoints.md",
            "adoption_class": "adopt_template",
            "mas_owner_surface": "quality_os_route_back_and_typed_blocker_refs",
            "required_contract_fields": [
                "checkpoint_type",
                "critical_gap_refs",
                "repair_round_count",
                "known_limitation_ref_after_budget_exhausted",
                "user_decision_ref_if_decision_point",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
        {
            "pattern_id": "progressive_disclosure_skill_bundle",
            "learned_from": "skills/*/SKILL.md + references/ + scripts/ + assets/",
            "adoption_class": "adopt_template",
            "mas_owner_surface": "mas_app_skill_and_domain_pack_skill_policy",
            "required_contract_fields": [
                "thin_entrypoint_ref",
                "referenced_detail_refs",
                "script_asset_refs",
                "trigger_scope",
                "forbidden_authority_effects",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
        {
            "pattern_id": "bounded_mode_registry",
            "learned_from": "MODE_REGISTRY.md",
            "adoption_class": "adopt_template",
            "mas_owner_surface": "stage_action_mode_discipline",
            "required_contract_fields": [
                "mode_id",
                "trigger_scope",
                "output_contract_ref",
                "non_default_mode_requires_explicit_owner_or_user_intent",
                "mode_registry_ref",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
        {
            "pattern_id": "source_search_discipline",
            "learned_from": "skills/light-literature-search/SKILL.md",
            "adoption_class": "adopt_contract",
            "mas_owner_surface": "source_readiness_and_literature_scout_refs",
            "required_contract_fields": [
                "source_family_refs",
                "query_strategy_refs",
                "mesh_or_controlled_vocab_ref_if_biomedical",
                "chinese_source_probe_ref_if_relevant",
                "provider_limitation_or_route_back_ref",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
        {
            "pattern_id": "data_access_level_to_sink_contract",
            "learned_from": "skills/light-data-engineering/SKILL.md",
            "adoption_class": "adopt_contract",
            "mas_owner_surface": "data_asset_os_and_public_sink_refs",
            "required_contract_fields": [
                "data_access_level_ref",
                "target_sink_ref",
                "allowed_use_ref",
                "deidentification_or_license_ref",
                "sink_authorization_ref_or_typed_blocker",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
        {
            "pattern_id": "citation_edge_and_retraction_check",
            "learned_from": "skills/light-citation/SKILL.md + skills/light-research-ethics/SKILL.md",
            "adoption_class": "adopt_contract",
            "mas_owner_surface": "citation_integrity_and_publication_ethics_refs",
            "required_contract_fields": [
                "citation_edge_ref",
                "edge_state_confirmed_not_in_open_index_or_unknown",
                "retraction_or_expression_of_concern_ref",
                "checked_source_refs",
                "manual_review_ref_if_high_stakes",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
        {
            "pattern_id": "citation_locator_audit",
            "learned_from": "skills/light-citation/references/locator_audit.md",
            "adoption_class": "adopt_contract",
            "mas_owner_surface": "citation_integrity_and_claim_evidence_refs",
            "required_contract_fields": [
                "claim_segment_id",
                "citation_ref",
                "locator_ref",
                "support_verdict",
                "rewrite_or_replace_ref_if_partial_or_unsupported",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
        {
            "pattern_id": "prisma_flow_count_reconciliation",
            "learned_from": "skills/light-literature-search/scripts/prisma_flow.py",
            "adoption_class": "adopt_template",
            "mas_owner_surface": "source_readiness_and_systematic_review_refs",
            "required_contract_fields": [
                "search_source_count_refs",
                "dedup_count_ref",
                "screening_exclusion_refs",
                "full_text_exclusion_reason_refs",
                "included_study_count_ref",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
        {
            "pattern_id": "figure_manifest_and_effective_font_check",
            "learned_from": "skills/light-figure-drawing/SKILL.md",
            "adoption_class": "adopt_template",
            "mas_owner_surface": "display_to_claim_and_paper_presentation_refs",
            "required_contract_fields": [
                "figure_manifest_ref",
                "target_journal_or_column_ref",
                "effective_font_size_check_ref",
                "export_format_ref",
                "caption_binding_ref",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
        {
            "pattern_id": "experiment_matrix_data_asset_backlink",
            "learned_from": "skills/light-research-plan/SKILL.md + skills/light-data-engineering/SKILL.md",
            "adoption_class": "adopt_template",
            "mas_owner_surface": "experiment_os_analysis_campaign_and_data_asset_refs",
            "required_contract_fields": [
                "experiment_matrix_ref",
                "robustness_or_sensitivity_ref",
                "derived_dataset_ref",
                "data_asset_backlink_ref",
                "analysis_owner_route_ref",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
        {
            "pattern_id": "statistical_analysis_triage",
            "learned_from": "skills/light-result-analysis/SKILL.md",
            "adoption_class": "adopt_template",
            "mas_owner_surface": "evaluation_os_and_statistical_analysis_refs",
            "required_contract_fields": [
                "effect_size_ref",
                "confidence_interval_ref",
                "multiplicity_or_fdr_ref",
                "leakage_or_overfit_check_ref",
                "analysis_repair_hint_ref",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
        {
            "pattern_id": "overclaim_lint_structured_findings",
            "learned_from": "skills/light-paper-polishing/SKILL.md",
            "adoption_class": "adopt_template",
            "mas_owner_surface": "manuscript_argument_and_reviewer_briefing_refs",
            "required_contract_fields": [
                "claim_strength_warning_ref",
                "finding_severity_ref",
                "language_tool_or_mechanical_check_ref",
                "medical_term_false_positive_note",
                "reviewer_repair_hint_ref",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
        {
            "pattern_id": "style_fingerprint_author_voice_hint",
            "learned_from": "skills/light-paper-polishing/scripts/style_fingerprint.py",
            "adoption_class": "watch_only",
            "mas_owner_surface": "manuscript_argument_and_reviewer_briefing_refs",
            "required_contract_fields": [
                "reference_style_profile_ref",
                "draft_style_profile_ref",
                "deviation_hint_ref",
                "author_voice_preservation_note",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
        {
            "pattern_id": "argument_review_claim_evidence_boundary",
            "learned_from": "skills/light-paper-polishing/references/argument_review.md",
            "adoption_class": "adopt_template",
            "mas_owner_surface": "manuscript_argument_and_claim_boundary_refs",
            "required_contract_fields": [
                "claim_ref",
                "evidence_ref",
                "boundary_ref",
                "hedging_calibration_ref",
                "section_role_ref",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
        {
            "pattern_id": "figure_integrity_lint_warning_ref",
            "learned_from": "skills/light-figure-drawing/references/figure_integrity.md + scripts/figure_integrity_lint.py",
            "adoption_class": "adopt_template",
            "mas_owner_surface": "display_to_claim_and_figure_evidence_refs",
            "required_contract_fields": [
                "figure_ref",
                "integrity_warning_ref",
                "axis_or_errorbar_policy_ref",
                "caption_disclosure_ref",
                "display_owner_action_ref",
            ],
            "may_block_unrelated_owner_dispatch": False,
        },
    ]


def _light_materializer_contract() -> dict[str, object]:
    return build_light_materializer_contract()


def _light_forbidden_authority() -> dict[str, bool]:
    return {
        "may_authorize_publication_readiness": False,
        "may_authorize_quality_verdict": False,
        "may_authorize_source_readiness": False,
        "may_sign_owner_receipt": False,
        "may_mutate_artifacts": False,
        "may_admit_route": False,
        "may_write_domain_truth": False,
        "may_create_or_replace_stage_router": False,
        "may_create_default_skill_inventory": False,
        "may_block_dispatch_for_missing_skill_engineering_advisory": False,
    }


def _light_missing_ref_policy() -> list[dict[str, object]]:
    return [
        {
            "missing_ref_class": "advisory_signal_ref",
            "blocks_current_delta": False,
            "blocks_unrelated_owner_dispatch": False,
            "response": "skip_or_emit_repair_hint",
            "typed_blocker_id": None,
        },
        {
            "missing_ref_class": "evidence_log_ref",
            "blocks_current_delta": False,
            "blocks_unrelated_owner_dispatch": False,
            "response": "skip_or_emit_repair_hint",
            "typed_blocker_id": None,
        },
        {
            "missing_ref_class": "skill_engineering_advisory_ref",
            "blocks_current_delta": False,
            "blocks_unrelated_owner_dispatch": False,
            "response": "skip_or_emit_repair_hint",
            "typed_blocker_id": None,
        },
        {
            "missing_ref_class": "progress_passport_ref",
            "blocks_current_delta": False,
            "blocks_unrelated_owner_dispatch": False,
            "response": "use_mas_stage_attempt_ledger_or_owner_receipt_refs",
            "typed_blocker_id": None,
        },
        {
            "missing_ref_class": "route_required_ref_for_current_delta",
            "blocks_current_delta": True,
            "blocks_unrelated_owner_dispatch": False,
            "response": "typed_blocker",
            "typed_blocker_id": "external_pattern_intake_route_required_ref_blocker",
        },
    ]


def _light_progress_first_policy() -> dict[str, object]:
    return {
        "advisory_or_evidence_log_missing_behavior": "skip_or_repair_hint",
        "skill_engineering_missing_behavior": "skip_or_repair_hint",
        "may_block_unrelated_owner_dispatch": False,
        "typed_blocker_only_when": "current_delta_route_required_ref_missing",
        "default_invocation": "none",
        "default_design": "ordinary_progress_has_no_extra_advisory_stage",
        "invocation_only_when": "current_delta_route_required_ref_missing_or_owner_action_requests_ref_family",
        "pipeline_orchestrator_policy": "use_mas_stage_owner_route_not_light_orchestrator",
        "passport_policy": "map_to_mas_stage_attempt_ledger_and_owner_receipt_refs",
        "mode_registry_policy": "bounded_entrypoint_hint_not_mas_route_table",
    }


def _light_skill_engineering_policy() -> dict[str, object]:
    return {
        "source_project_role": "pattern_source_only",
        "accepted_methods": [
            "progress_passport_ref_ledger",
            "checkpoint_gate_budget",
            "progressive_disclosure_skill_bundle",
            "bounded_mode_registry",
            "source_search_discipline",
            "data_access_level_to_sink_contract",
            "citation_edge_and_retraction_check",
            "citation_locator_audit",
            "prisma_flow_count_reconciliation",
            "figure_manifest_and_effective_font_check",
            "experiment_matrix_data_asset_backlink",
            "statistical_analysis_triage",
            "overclaim_lint_structured_findings",
            "style_fingerprint_author_voice_hint",
            "argument_review_claim_evidence_boundary",
            "figure_integrity_lint_warning_ref",
        ],
        "accepted_ref_classes": [
            "skill_engineering_advisory_ref",
            "progress_passport_ref",
            "source_search_discipline_ref",
            "data_access_sink_ref",
            "citation_edge_retraction_ref",
            "citation_locator_audit_ref",
            "prisma_flow_reconciliation_ref",
            "figure_manifest_check_ref",
            "experiment_matrix_backlink_ref",
            "statistical_analysis_triage_ref",
            "overclaim_lint_warning_ref",
            "style_fingerprint_hint_ref",
            "argument_review_hint_ref",
            "figure_integrity_warning_ref",
        ],
        "passport_maps_to": "mas_stage_attempt_ledger_and_owner_receipt_refs",
        "checkpoint_maps_to": "route_back_typed_blocker_human_gate_or_known_limitation_refs",
        "mode_registry_maps_to": "bounded_skill_entrypoint_modes_not_stage_router",
        "progressive_disclosure_maps_to": "thin_mas_skill_entrypoint_plus_referenced_contract_refs",
        "style_fingerprint_maps_to": "reviewer_or_writing_hint_only",
        "argument_review_maps_to": "claim_evidence_boundary_and_hedging_hint_only",
        "figure_integrity_lint_maps_to": "display_reviewer_warning_or_route_required_ref_only",
        "missing_behavior": "skip_or_repair_hint",
        "progress_first_non_blocking": True,
        "forbidden_imports": [
            "light_runtime",
            "light_orchestrator_as_mas_route_owner",
            "light_27_skill_router",
            "light_db09_or_project_memory_as_mas_truth",
            "light_scores_or_checklists_as_quality_gate",
        ],
    }


def _journal_acceptance_evidence_fields(pack_id: str) -> list[dict[str, object]]:
    return [
        _field(field_id, role)
        for field_id, role in _JOURNAL_ACCEPTANCE_EVIDENCE_FIELDS[pack_id]
    ]


def _journal_required_reviewer_output(pack_id: str) -> list[dict[str, object]]:
    return [
        {
            "output_id": output_id,
            "role": role,
            "required": True,
            "may_authorize_publication_readiness": False,
            "may_authorize_quality_verdict": False,
        }
        for output_id, role in _JOURNAL_REQUIRED_REVIEWER_OUTPUTS[pack_id]
    ]


def _journal_forbidden_authority() -> list[dict[str, object]]:
    return [
        {
            "authority_id": authority_id,
            "forbidden": True,
            "reason": reason,
        }
        for authority_id, reason in (
            ("vendor_skill_authority", "clean_room_pattern_only"),
            ("runtime_authority", "opl_descriptor_ref_locator_only"),
            ("default_skill_authority", "journal_pack_must_be_explicitly_consumed"),
            ("publication_readiness_authority", "mas_owner_receipt_or_reviewer_record_required"),
            ("quality_verdict_authority", "mas_quality_owner_closure_required"),
            ("mas_truth_write_authority", "pack_is_reviewer_rubric_not_truth_writer"),
        )
    ]


def _journal_quality_pack_consumption(pack_id: str) -> dict[str, object]:
    return {
        "consumer_roles": ["reviewer_agent", "auditor_agent"],
        "consumed_as": "explicit_quality_pack_descriptor",
        "required_contract_refs": [ref["ref"] for ref in _PACK_REQUIRED_REFS[pack_id]],
        "required_output_classes": [
            output_id for output_id, _role in _JOURNAL_REQUIRED_REVIEWER_OUTPUTS[pack_id]
        ],
        "opl_consumption_role": "descriptor_ref_freshness_locator_only",
        "opl_may_authorize_quality_verdict": False,
        "opl_may_authorize_publication_readiness": False,
        "opl_may_write_mas_truth": False,
    }


def _field(field_id: str, role: str) -> dict[str, object]:
    return {"field_id": field_id, "role": role, "required": True}


__all__ = [
    "CLINICAL_BASE_GUIDELINES",
    "CONTRACT_REF",
    "JOURNAL_FAMILY_QUALITY_PACK_IDS",
    "PACK_ROLE",
    "PROJECTION_KIND",
    "QUALITY_PACK_CONTRACT_SURFACES",
    "REFRESH_POLICY",
    "REPO_PATH",
    "REQUIRED_STAGE_QUALITY_PACK_IDS",
    "STRONG_PROMOTION_EVIDENCE_KINDS",
    "SURFACE_KIND",
    "VERSION",
    "build_stage_quality_pack_contract",
    "build_stage_quality_pack_locator_projection",
    "build_stage_quality_pack_projection",
    "build_stage_quality_pack_ref_projection",
    "quality_pack_ids_for_stages",
]
