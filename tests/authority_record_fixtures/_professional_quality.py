"""Professional skill and first-draft quality fixture builders."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from ._primitives import PrimitiveAuthorityFixtures
from .surface_constants import (
    FIRST_DRAFT_ROLE_BY_REF_FIELD,
    LEGACY_FIRST_DRAFT_ROLE_BY_REF_FIELD,
    SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL,
)


class ProfessionalQualityFixtures(PrimitiveAuthorityFixtures):

    @classmethod
    def scholar_v2_semantic_policy_bindings(
        cls,
        invocations: list[dict[str, Any]],
        candidate_refs: dict[str, dict[str, Any] | None],
    ) -> list[dict[str, Any]]:
        invocations_by_skill = {
            item["skill_id"]: item
            for item in invocations
            if item["surface_kind"]
            == "mas_professional_manuscript_skill_invocation_candidate"
        }
        bindings = []
        for skill_id, policy in SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL.items():
            invocation = invocations_by_skill[skill_id]
            candidate_ref = candidate_refs[policy["candidate_ref_field"]]
            if candidate_ref is None:
                continue
            bindings.append(
                {
                    "skill_id": skill_id,
                    "semantic_policy_id": policy["policy_id"],
                    "validator_id": policy["validator_id"],
                    "semantic_policy_ref": deepcopy(
                        invocation["semantic_policy_ref"]
                    ),
                    "candidate_ref_field": policy["candidate_ref_field"],
                    "candidate_surface_kind": policy["candidate_surface_kind"],
                    "candidate_ref": deepcopy(invocation["semantic_candidate_ref"]),
                    "invocation_ref": deepcopy(invocation["invocation_ref"]),
                    "receipt_ref": deepcopy(invocation["receipt_ref"]),
                }
            )
        return sorted(bindings, key=lambda item: item["skill_id"])

    @classmethod
    def first_draft_quality_application(
        cls,
        artifacts: list[dict[str, Any]],
        *,
        schema_version: int = 2,
        paper_type: str = "prediction_model",
        validation_design: str = "internal_validation",
        reports_fixed_horizon_risk: bool = True,
        competing_risk_relevant: bool = True,
        reports_decision_curve_analysis: bool = True,
        includes_table_one: bool = True,
        requires_reader_pdf: bool = True,
        uses_clinical_or_registry_data: bool = True,
        include_scholar_v2_semantics: bool = False,
        disposition_overrides: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        artifacts_by_role = {artifact["role"]: artifact for artifact in artifacts}
        triggers = {
            "reports_fixed_horizon_risk": reports_fixed_horizon_risk,
            "competing_risk_relevant": competing_risk_relevant,
            "reports_decision_curve_analysis": reports_decision_curve_analysis,
            "includes_table_one": includes_table_one,
            "requires_reader_pdf": requires_reader_pdf,
        }
        if schema_version == 2:
            triggers["uses_clinical_or_registry_data"] = (
                uses_clinical_or_registry_data
            )
        applicable_fields = {
            "medical_initial_draft_preflight_candidate_ref",
            "citation_source_coverage_ref",
            "claim_guardrail_ref",
        }
        if include_scholar_v2_semantics:
            applicable_fields.update(
                {
                    "active_reference_currentness_ref",
                    "author_stance_integrity_ref",
                }
            )
        if uses_clinical_or_registry_data:
            applicable_fields.add("clinical_analysis_input_identity_ref")
        if paper_type == "prediction_model":
            applicable_fields.update(
                {
                    "validation_partition_integrity_ref",
                    "endpoint_analysis_set_reconciliation_ref",
                    "model_complexity_sparse_event_ref",
                }
            )
            if include_scholar_v2_semantics:
                applicable_fields.add("linked_prediction_performance_ref")
        if reports_fixed_horizon_risk:
            applicable_fields.add("fixed_horizon_risk_semantics_ref")
        if competing_risk_relevant:
            applicable_fields.add("competing_risk_ref")
        if reports_decision_curve_analysis:
            applicable_fields.add("decision_curve_validity_ref")
        if includes_table_one:
            applicable_fields.add("baseline_table_traceability_ref")
        if requires_reader_pdf:
            applicable_fields.add("document_display_scope_coverage_ref")
            if include_scholar_v2_semantics:
                applicable_fields.add("display_render_integrity_ref")
        if validation_design == "external_validation":
            applicable_fields.add("external_transportability_ref")

        role_by_ref_field = (
            FIRST_DRAFT_ROLE_BY_REF_FIELD
            if include_scholar_v2_semantics
            else LEGACY_FIRST_DRAFT_ROLE_BY_REF_FIELD
        )
        candidate_refs = {
            ref_field: (
                cls.mas_artifact_ref(artifacts_by_role[role])
                if ref_field in applicable_fields
                else None
            )
            for ref_field, role in role_by_ref_field.items()
        }
        application = {
            "surface_kind": "mas_first_draft_quality_application_candidate",
            "schema_version": schema_version,
            "paper_type": paper_type,
            "validation_design": validation_design,
            "triggers": triggers,
            "candidate_refs": candidate_refs,
        }
        if schema_version == 2:
            application["candidate_dispositions"] = {
                ref_field: (
                    {
                        "status": "satisfied",
                        "earliest_route_back_owner": None,
                        "reason_codes": [],
                        "unresolved_items": [],
                        "not_applicable_reason": None,
                    }
                    if ref_field in applicable_fields
                    else {
                        "status": "not_applicable_with_reason",
                        "earliest_route_back_owner": None,
                        "reason_codes": [],
                        "unresolved_items": [],
                        "not_applicable_reason": (
                            "The declared paper type or first-draft trigger does not "
                            "require this specialist candidate."
                        ),
                    }
                )
                for ref_field in role_by_ref_field
            }
            for ref_field, override in (disposition_overrides or {}).items():
                application["candidate_dispositions"][ref_field].update(
                    deepcopy(override)
                )
        return application

    @classmethod
    def professional_figure_skill_invocations(
        cls,
        artifacts: list[dict[str, Any]],
        *,
        figure_id: str = "F1",
        composition_mode: str = "single_canvas_direct",
        schema_version: int = 1,
    ) -> list[dict[str, Any]]:
        bindings = [
            {
                key: artifact[key]
                for key in ("member_id", "role", "ref", "size_bytes", "sha256")
            }
            for artifact in artifacts
            if artifact["role"] == "figure_file"
        ]
        if not bindings:
            return []
        common = {
            "surface_kind": "mas_professional_figure_skill_invocation_candidate",
            "schema_version": schema_version,
            "figure_id": figure_id,
            "figure_kind": "evidence_figure",
            "composition_mode": composition_mode,
            "package_id": "mas-scholar-skills",
            "package_version": "test-version",
            "package_source_ref": "git:mas-scholar-skills@test",
            "package_source_sha256": cls.digest("mas-scholar-skills:test-source"),
            "input_contract_ref": f"mas-figure-contract://{figure_id}",
            "input_sha256": cls.digest(f"figure-contract:{figure_id}"),
            "output_artifact_bindings": bindings,
            "status": "completed",
            "refs_only": True,
            "authority": False,
            "publication_ready": False,
        }
        invocations = []
        for skill_id in ("medical-figure-design", "medical-figure-style"):
            invocation = {
                **deepcopy(common),
                "skill_id": skill_id,
                "skill_source_ref": f"skills/{skill_id}/SKILL.md",
                "skill_source_sha256": cls.digest(f"skill-source:{skill_id}"),
                "invocation_id": f"invocation:{figure_id}:{skill_id}",
                "consumed_rule_refs": [f"{skill_id}#workflow"],
            }
            if skill_id == "medical-figure-design":
                invocation["template_usage"] = {
                    "used": False,
                    "decision_reason": "No reusable template was consumed.",
                }
                invocation["figure_text_policy"] = {
                    "embedded_title": False,
                    "embedded_subtitle": False,
                    "embedded_prose_footer": False,
                    "allowed_text_roles": [
                        "panel_label",
                        "axis_label",
                        "tick_label",
                        "legend",
                        "necessary_statistical_annotation",
                    ],
                }
            if schema_version == 2:
                input_bindings = [
                    cls.artifact_binding(artifact)
                    for artifact in artifacts
                    if artifact["role"] in {"analysis_output", "figure_catalog"}
                ]
                invocation["input_artifact_bindings"] = input_bindings
                receipt_ref = cls.professional_receipt_ref(
                    {
                        "skill_id": skill_id,
                        "figure_id": figure_id,
                        "skill_source_sha256": invocation["skill_source_sha256"],
                        "input_artifact_bindings": input_bindings,
                        "output_artifact_bindings": invocation[
                            "output_artifact_bindings"
                        ],
                        "consumed_rule_refs": invocation["consumed_rule_refs"],
                        "status": "completed",
                    }
                )
                invocation["receipt_id"] = receipt_ref["ref"]
                invocation["receipt_ref"] = receipt_ref
                invocation["invocation_ref"] = cls.professional_invocation_ref(
                    invocation
                )
            else:
                invocation["receipt_id"] = (
                    f"mas-professional-figure-skill:{figure_id}:{skill_id}"
                )
            invocations.append(invocation)
        if composition_mode == "assembled_panels":
            invocation = {
                **deepcopy(common),
                "skill_id": "medical-figure-composer",
                "skill_source_ref": "skills/medical-figure-composer/SKILL.md",
                "skill_source_sha256": cls.digest(
                    "skill-source:medical-figure-composer"
                ),
                "invocation_id": f"invocation:{figure_id}:medical-figure-composer",
                "consumed_rule_refs": ["medical-figure-composer#workflow"],
            }
            if schema_version == 2:
                input_bindings = [
                    cls.artifact_binding(artifact)
                    for artifact in artifacts
                    if artifact["role"] in {"analysis_output", "figure_catalog"}
                ]
                invocation["input_artifact_bindings"] = input_bindings
                receipt_ref = cls.professional_receipt_ref(
                    {
                        "skill_id": "medical-figure-composer",
                        "figure_id": figure_id,
                        "skill_source_sha256": invocation["skill_source_sha256"],
                        "input_artifact_bindings": input_bindings,
                        "output_artifact_bindings": invocation[
                            "output_artifact_bindings"
                        ],
                        "consumed_rule_refs": invocation["consumed_rule_refs"],
                        "status": "completed",
                    }
                )
                invocation["receipt_id"] = receipt_ref["ref"]
                invocation["receipt_ref"] = receipt_ref
                invocation["invocation_ref"] = cls.professional_invocation_ref(
                    invocation
                )
            else:
                invocation["receipt_id"] = (
                    f"mas-professional-figure-skill:{figure_id}:"
                    "medical-figure-composer"
                )
            invocations.append(invocation)
        return invocations

    @classmethod
    def professional_manuscript_skill_invocations(
        cls,
        artifacts: list[dict[str, Any]],
        *,
        schema_version: int = 1,
        include_scholar_v2_semantics: bool = False,
    ) -> list[dict[str, Any]]:
        artifact_by_role = {artifact["role"]: artifact for artifact in artifacts}
        role_sets = {
            "medical-manuscript-writing": {
                "canonical_manuscript",
                "claim_evidence_map",
                "claim_guardrail",
                "medical_initial_draft_preflight_candidate",
                "author_stance_integrity",
            },
            "medical-registry-atlas-story-architect": {
                "canonical_manuscript",
                "claim_evidence_map",
            },
            "medical-data-freeze-and-analysis-readiness-reviewer": {
                "clinical_analysis_input_identity"
            },
            "medical-reference-integrity-auditor": {"citation_source_coverage"},
            "medical-statistical-review": {
                "analysis_output",
                "numeric_trace",
                "validation_partition_integrity",
                "endpoint_analysis_set_reconciliation",
                "model_complexity_sparse_event",
                "decision_curve_validity",
            },
            "medical-survival-analysis-plan": {
                "fixed_horizon_risk_semantics",
                "competing_risk",
            },
            "medical-risk-model-transportability-reviewer": {
                "external_transportability"
            },
            "medical-table-design": {
                "table_catalog",
                "table_file",
                "baseline_table_traceability",
            },
            "medical-display-qc": {"document_display_scope_coverage", "pdf"},
            "medical-submission-prep": {
                "canonical_manuscript",
                "docx",
                "pdf",
                "supplementary_output",
                "final_zip_allowlist",
                "final_zip_member",
            },
        }
        if include_scholar_v2_semantics:
            role_sets["medical-reference-integrity-auditor"].add(
                "active_reference_currentness"
            )
            role_sets["medical-statistical-review"].add(
                "linked_prediction_performance"
            )
            role_sets["medical-display-qc"].add("display_render_integrity")
        input_role_sets = {
            "medical-manuscript-writing": {
                "medical_initial_draft_preflight_candidate",
                "clinical_analysis_input_identity",
                "citation_source_coverage",
                "claim_guardrail",
            },
            "medical-registry-atlas-story-architect": {"claim_evidence_map"},
            "medical-data-freeze-and-analysis-readiness-reviewer": {
                "source_input_digest",
                "data_release",
                "denominator_definitions",
            },
            "medical-reference-integrity-auditor": {
                "citation_ledger",
                "reference_library",
            },
            "medical-statistical-review": {
                "data_release",
                "denominator_definitions",
                "analysis_output",
                "numeric_trace",
            },
            "medical-survival-analysis-plan": {
                "denominator_definitions",
                "analysis_output",
                "numeric_trace",
            },
            "medical-risk-model-transportability-reviewer": {
                "data_release",
                "denominator_definitions",
                "analysis_output",
            },
            "medical-table-design": {"analysis_output", "numeric_trace"},
            "medical-display-qc": {"canonical_manuscript", "pdf"},
            "medical-submission-prep": {"canonical_manuscript"},
        }
        invocations = []
        for skill_id, roles in role_sets.items():
            if skill_id == "medical-submission-prep" and not any(
                artifact["role"] in {"docx", "pdf", "supplementary_output"}
                for artifact in artifacts
            ):
                continue
            bindings = [
                {
                    key: artifact[key]
                    for key in ("member_id", "role", "ref", "size_bytes", "sha256")
                }
                for artifact in artifacts
                if artifact["role"] in roles
            ]
            if not bindings:
                continue
            invocation = {
                "surface_kind": (
                    "mas_professional_manuscript_skill_invocation_candidate"
                ),
                "schema_version": schema_version,
                "skill_id": skill_id,
                "package_id": "mas-scholar-skills",
                "package_version": "test-version",
                "package_source_ref": "git:mas-scholar-skills@test",
                "package_source_sha256": cls.digest(
                    "mas-scholar-skills:test-source"
                ),
                "skill_source_ref": f"skills/{skill_id}/SKILL.md",
                "skill_source_sha256": cls.digest(f"skill-source:{skill_id}"),
                "invocation_id": f"invocation:first-draft:{skill_id}",
                "input_contract_ref": "mas-manuscript-contract://first-draft",
                "input_sha256": cls.digest("manuscript-contract:first-draft"),
                "consumed_rule_refs": [
                    f"{skill_id}#workflow",
                    *(
                        ["medical-table-design#main-table-information-budget"]
                        if skill_id == "medical-table-design"
                        else []
                    ),
                ],
                "output_artifact_bindings": bindings,
                "template_substitution": False,
                "status": "completed",
                "refs_only": True,
                "authority": False,
                "publication_ready": False,
                **(
                    {
                        "table_quality_application": {
                            "schema_version": 1,
                            "policy_ref": "medical-table-design#main-table-information-budget",
                            "template_policy": "reference_floor_not_required",
                            "coverage_status": "all_main_tables_assessed",
                            "main_tables": [
                                {
                                    "table_id": "T1",
                                    "role": "main_text",
                                    "reader_question": "Who is represented in the cohort?",
                                    "row_count": 7,
                                    "column_count": 8,
                                    "body_word_count": 202,
                                    "max_cell_word_count": 12,
                                    "footnote_word_count": 18,
                                    "supplementary_detail_refs": ["TS27"],
                                    "budget_status": "within_default_budget",
                                    "exception_reason": None,
                                    "final_embedding_status": "passed",
                                    "final_embedding_page_span": 1,
                                    "standalone_notes_heading_present": False,
                                }
                            ],
                        }
                    }
                    if skill_id == "medical-table-design"
                    else {}
                ),
            }
            if schema_version == 2:
                policy = SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL.get(skill_id)
                if (
                    include_scholar_v2_semantics
                    and policy is not None
                    and FIRST_DRAFT_ROLE_BY_REF_FIELD[
                        policy["candidate_ref_field"]
                    ]
                    in artifact_by_role
                ):
                    semantic_candidate = cls.mas_artifact_ref(
                        artifact_by_role[
                            FIRST_DRAFT_ROLE_BY_REF_FIELD[
                                policy["candidate_ref_field"]
                            ]
                        ]
                    )
                    invocation["semantic_policy_id"] = policy["policy_id"]
                    invocation["semantic_validator_id"] = policy["validator_id"]
                    invocation["semantic_policy_ref"] = cls.exact_ref(
                        "scholarskills_semantic_policy", policy["policy_id"]
                    )
                    invocation["semantic_candidate_ref"] = semantic_candidate
                    invocation["consumed_rule_refs"].extend(
                        [
                            policy["policy_id"],
                            f"validator:{policy['validator_id']}",
                        ]
                    )
                input_bindings = [
                    cls.artifact_binding(artifact)
                    for artifact in artifacts
                    if artifact["role"] in input_role_sets[skill_id]
                ]
                invocation["input_artifact_bindings"] = input_bindings
                receipt_core = {
                    "skill_id": skill_id,
                    "skill_source_sha256": invocation["skill_source_sha256"],
                    "input_artifact_bindings": input_bindings,
                    "output_artifact_bindings": invocation[
                        "output_artifact_bindings"
                    ],
                    "consumed_rule_refs": invocation["consumed_rule_refs"],
                    "status": "completed",
                }
                if "semantic_policy_id" in invocation:
                    receipt_core.update(
                        {
                            "semantic_policy_id": invocation[
                                "semantic_policy_id"
                            ],
                            "semantic_validator_id": invocation[
                                "semantic_validator_id"
                            ],
                            "semantic_policy_ref": invocation[
                                "semantic_policy_ref"
                            ],
                            "semantic_candidate_ref": invocation[
                                "semantic_candidate_ref"
                            ],
                        }
                    )
                receipt_ref = cls.professional_receipt_ref(receipt_core)
                invocation["receipt_id"] = receipt_ref["ref"]
                invocation["receipt_ref"] = receipt_ref
                invocation["invocation_ref"] = cls.professional_invocation_ref(
                    invocation
                )
            else:
                invocation["receipt_id"] = (
                    f"mas-professional-manuscript-skill:{skill_id}"
                )
            invocations.append(invocation)
        return invocations
