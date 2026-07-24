from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any

import pytest


ANALYSIS_ROLES = (
    "source_input_digest",
    "data_release",
    "denominator_definitions",
    "analysis_script",
    "analysis_output",
)
MANUSCRIPT_ROLES = ANALYSIS_ROLES + (
    "candidate_admission_receipt",
    "canonical_manuscript",
    "claim_evidence_map",
    "citation_ledger",
    "numeric_trace",
    "reference_library",
    "table_catalog",
    "table_file",
    "figure_catalog",
    "figure_file",
    "render_environment_and_font_manifest",
)
FIRST_DRAFT_QUALITY_ROLES = (
    "medical_initial_draft_preflight_candidate",
    "clinical_analysis_input_identity",
    "citation_source_coverage",
    "validation_partition_integrity",
    "endpoint_analysis_set_reconciliation",
    "model_complexity_sparse_event",
    "fixed_horizon_risk_semantics",
    "competing_risk",
    "decision_curve_validity",
    "baseline_table_traceability",
    "document_display_scope_coverage",
    "claim_guardrail",
    "author_stance_integrity",
)
LEGACY_FIRST_DRAFT_ROLE_BY_REF_FIELD = {
    "medical_initial_draft_preflight_candidate_ref": (
        "medical_initial_draft_preflight_candidate"
    ),
    "clinical_analysis_input_identity_ref": "clinical_analysis_input_identity",
    "citation_source_coverage_ref": "citation_source_coverage",
    "validation_partition_integrity_ref": "validation_partition_integrity",
    "endpoint_analysis_set_reconciliation_ref": (
        "endpoint_analysis_set_reconciliation"
    ),
    "model_complexity_sparse_event_ref": "model_complexity_sparse_event",
    "fixed_horizon_risk_semantics_ref": "fixed_horizon_risk_semantics",
    "competing_risk_ref": "competing_risk",
    "decision_curve_validity_ref": "decision_curve_validity",
    "baseline_table_traceability_ref": "baseline_table_traceability",
    "document_display_scope_coverage_ref": "document_display_scope_coverage",
    "claim_guardrail_ref": "claim_guardrail",
    "external_transportability_ref": "external_transportability",
}
SCHOLAR_V2_FIRST_DRAFT_ROLE_BY_REF_FIELD = {
    "active_reference_currentness_ref": "active_reference_currentness",
    "linked_prediction_performance_ref": "linked_prediction_performance",
    "display_render_integrity_ref": "display_render_integrity",
    "author_stance_integrity_ref": "author_stance_integrity",
}
FIRST_DRAFT_ROLE_BY_REF_FIELD = {
    **LEGACY_FIRST_DRAFT_ROLE_BY_REF_FIELD,
    **SCHOLAR_V2_FIRST_DRAFT_ROLE_BY_REF_FIELD,
}
SELECTED_BUILD_ROLE_BY_REF_FIELD = {
    "selected_archive_manifest_ref": "selected_archive_manifest",
    "selected_build_receipt_ref": "selected_build_receipt",
    "dependency_manifest_ref": "build_dependency_manifest",
    "root_reader_output_ref": "root_reader_output",
    "selected_reader_output_ref": "selected_reader_output",
}
REVIEWER_RESPONSE_ROLE_BY_REF_FIELD = {
    "response_ref": "reviewer_response",
    "action_matrix_ref": "reviewer_action_matrix",
    "artifact_inventory_ref": "reviewer_artifact_inventory",
    "external_synthesis_ref": "reviewer_external_synthesis",
    "new_revision_ref": "reviewer_new_revision",
}
SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL = {
    "medical-manuscript-writing": {
        "policy_id": "scholarskills_medical_initial_draft_preflight.v3",
        "validator_id": "validate_medical_initial_draft_preflight_candidate_v3",
        "candidate_ref_field": "medical_initial_draft_preflight_candidate_ref",
        "candidate_surface_kind": "medical_initial_draft_preflight_candidate_ref",
    },
    "medical-statistical-review": {
        "policy_id": "scholarskills_linked_prediction_performance.v2",
        "validator_id": "validate_linked_prediction_performance",
        "candidate_ref_field": "linked_prediction_performance_ref",
        "candidate_surface_kind": "linked_prediction_performance_ref",
    },
    "medical-reference-integrity-auditor": {
        "policy_id": "scholarskills_medical_initial_draft_preflight.v2",
        "validator_id": "audit_active_reference_currentness",
        "candidate_ref_field": "active_reference_currentness_ref",
        "candidate_surface_kind": "active_reference_currentness_ref",
    },
    "medical-display-qc": {
        "policy_id": "scholarskills_medical_initial_draft_preflight.v2",
        "validator_id": "validate_display_render_integrity",
        "candidate_ref_field": "display_render_integrity_ref",
        "candidate_surface_kind": "display_render_integrity_ref",
    },
}
PUBLICATION_ROLES = MANUSCRIPT_ROLES + (
    "docx",
    "pdf",
    "supplementary_output",
    "final_zip_allowlist",
    "final_zip_member",
    "submission_status",
    "publication_evaluation",
    "next_action_envelope",
    "submission_projection_manifest",
)
ROLES_BY_SCOPE = {
    "analysis_generation": ANALYSIS_ROLES,
    "manuscript_generation": MANUSCRIPT_ROLES,
    "publication_generation": PUBLICATION_ROLES,
}
LANES_BY_SCOPE = {
    "analysis_generation": ("statistical",),
    "manuscript_generation": ("medical", "statistical", "reference", "display"),
    "publication_generation": (
        "medical",
        "statistical",
        "reference",
        "display",
        "publication",
        "exact_byte_package",
    ),
}
AUTHORITY_ROLE_BY_LANE = {
    "medical": "mas_independent_medical_reviewer",
    "statistical": "mas_independent_statistical_reviewer",
    "reference": "mas_independent_reference_reviewer",
    "display": "mas_independent_display_reviewer",
    "publication": "mas_independent_publication_reviewer",
    "exact_byte_package": "mas_independent_exact_byte_package_reviewer",
}


class AuthorityRecordFactory:
    authority_epoch = "mas-authority-epoch-2026-07-15"
    generation_id = "study-generation-003"

    @staticmethod
    def canonical_bytes(payload: dict[str, Any]) -> bytes:
        return json.dumps(
            payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")

    @classmethod
    def digest(cls, value: str | bytes) -> str:
        encoded = value.encode("utf-8") if isinstance(value, str) else value
        return f"sha256:{hashlib.sha256(encoded).hexdigest()}"

    @classmethod
    def fingerprint(cls, payload: dict[str, Any]) -> str:
        return cls.digest(cls.canonical_bytes(payload))

    @classmethod
    def review_snapshot_authority_issuer(cls) -> dict[str, Any]:
        return {
            "agent_id": "mas",
            "domain_id": "medautoscience",
            "package_id": "mas",
            "stage_attempt_ref": "opl://stage_attempts/producer-attempt-001",
            "execution_content_binding_sha256": cls.digest(
                "producer-attempt-execution-content-binding"
            ),
            "package_use_boundary_id": "package-use:producer-attempt-001",
            "root_package_content_digest": cls.digest("mas-package-content"),
        }

    @classmethod
    def typed_ref(cls, kind: str, name: str) -> dict[str, Any]:
        return {
            "kind": kind,
            "ref": f"{kind}://{name}",
            "sha256": cls.digest(f"{kind}:{name}:bytes"),
        }

    @classmethod
    def exact_ref(
        cls,
        kind: str,
        name: str,
        *,
        size_bytes: int | None = None,
        sha256: str | None = None,
    ) -> dict[str, Any]:
        return {
            "kind": kind,
            "ref": f"{kind}://{name}",
            "size_bytes": size_bytes if size_bytes is not None else 100 + len(name),
            "sha256": sha256 or cls.digest(f"{kind}:{name}:bytes"),
        }

    @staticmethod
    def no_authority_boundary() -> dict[str, bool]:
        return {"authorizes_publication": False, "authorizes_submission": False}

    @staticmethod
    def artifact_exact_ref(artifact: dict[str, Any]) -> dict[str, Any]:
        return {
            "kind": "mas_artifact",
            "ref": artifact["ref"],
            "size_bytes": artifact["size_bytes"],
            "sha256": artifact["sha256"],
        }

    @staticmethod
    def affected_artifact_binding(artifact: dict[str, Any]) -> dict[str, Any]:
        return {
            "member_id": artifact["member_id"],
            "ref": artifact["ref"],
            "size_bytes": artifact["size_bytes"],
            "sha256": artifact["sha256"],
        }

    @classmethod
    def seal(cls, core: dict[str, Any], prefix: str) -> dict[str, Any]:
        receipt_fingerprint = cls.fingerprint(core)
        return {
            **deepcopy(core),
            "receipt_id": f"{prefix}:{receipt_fingerprint.removeprefix('sha256:')}",
            "receipt_size_bytes": len(cls.canonical_bytes(core)),
            "receipt_fingerprint": receipt_fingerprint,
        }

    @classmethod
    def receipt_ref(cls, kind: str, receipt: dict[str, Any]) -> dict[str, Any]:
        return {
            "kind": kind,
            "ref": receipt["receipt_id"],
            "size_bytes": receipt["receipt_size_bytes"],
            "sha256": receipt["receipt_fingerprint"],
        }

    @classmethod
    def build_dependency_currentness_authority(
        cls,
        dependency_manifest_ref: dict[str, Any],
        dependency_currentness: str,
        reviewer_response_currentness: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        from med_autoscience.authority_handlers.build_dependency_currentness import (
            evaluate_build_dependency_currentness_authority,
        )

        request = cls.build_dependency_currentness_authority_request(
            dependency_manifest_ref,
            dependency_currentness,
            reviewer_response_currentness,
        )
        result = evaluate_build_dependency_currentness_authority(request)
        if result["status"] != "owner_authority":
            raise AssertionError(result)
        return {
            "authority_ref": deepcopy(result["authority_ref"]),
            "authority_record": deepcopy(result["authority_record"]),
        }

    @classmethod
    def build_dependency_currentness_authority_request(
        cls,
        dependency_manifest_ref: dict[str, Any],
        dependency_currentness: str,
        reviewer_response_currentness: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        reviewer_response_currentness = reviewer_response_currentness or {
            "generation_id": cls.generation_id,
            "candidate_state": "pre_freeze",
            "response_ref": cls.exact_ref(
                "mas_artifact", "reviewer-response-current"
            ),
            "prior_frozen_response_ref": None,
            "post_freeze_disposition": "not_started",
            "external_synthesis_ref": None,
            "new_revision_ref": None,
            "owner_ledger_history_ref": cls.exact_ref(
                "opl_action_output", "build-dependency-currentness-owner-ledger"
            ),
        }
        return {
            "surface_kind": "mas_build_dependency_currentness_authority_request",
            "schema_version": 1,
            "authority_context": {
                "action_id": "build_dependency_currentness_authority_evaluate",
                "authority_epoch": cls.authority_epoch,
                "managed_authority_attempt_ref": cls.typed_ref(
                    "opl_stage_attempt", "build-dependency-currentness-owner"
                ),
                "generation_producer_attempt_ref": cls.typed_ref(
                    "opl_stage_attempt", "paper-producer"
                ),
                "managed_authority_attempt_receipt_ref": cls.exact_ref(
                    "opl_action_output", "build-dependency-currentness-attempt"
                ),
                "owner_ledger_ref": cls.exact_ref(
                    "opl_action_output", "build-dependency-currentness-owner-ledger"
                ),
            },
            "dependency_manifest_ref": deepcopy(dependency_manifest_ref),
            "dependency_currentness": dependency_currentness,
            "reviewer_response_currentness": deepcopy(
                reviewer_response_currentness
            ),
        }

    @staticmethod
    def artifact_binding(artifact: dict[str, Any]) -> dict[str, Any]:
        return {
            key: artifact[key]
            for key in ("member_id", "role", "ref", "size_bytes", "sha256")
        }

    @classmethod
    def mas_artifact_ref(cls, artifact: dict[str, Any]) -> dict[str, Any]:
        return {
            "kind": "mas_artifact",
            "ref": artifact["ref"],
            "size_bytes": artifact["size_bytes"],
            "sha256": artifact["sha256"],
        }

    @classmethod
    def professional_invocation_ref(
        cls,
        invocation_core: dict[str, Any],
    ) -> dict[str, Any]:
        invocation_sha256 = cls.fingerprint(invocation_core)
        return {
            "kind": "mas_professional_skill_invocation",
            "ref": (
                "mas-professional-skill-invocation:"
                f"{invocation_sha256.removeprefix('sha256:')}"
            ),
            "size_bytes": len(cls.canonical_bytes(invocation_core)),
            "sha256": invocation_sha256,
        }

    @classmethod
    def professional_receipt_ref(
        cls,
        receipt_core: dict[str, Any],
    ) -> dict[str, Any]:
        receipt_sha256 = cls.fingerprint(receipt_core)
        return {
            "kind": "scholarskills_professional_skill_receipt",
            "ref": (
                "scholarskills-professional-skill-receipt:"
                f"{receipt_sha256.removeprefix('sha256:')}"
            ),
            "size_bytes": len(cls.canonical_bytes(receipt_core)),
            "sha256": receipt_sha256,
        }

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
    def epistemic_currentness(
        cls,
        manifest: dict[str, Any],
        lane: str,
        *,
        invalidating_changes: list[dict[str, Any]] | None = None,
        ignored_changes: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        from med_autoscience.authority_handlers._generation_manifest import (
            epistemic_review_dependency_refs,
        )

        scope = next(
            item["epistemic_scope"]
            for item in manifest["review_scopes"]
            if item["review_lane"] == lane
        )
        invalidating = deepcopy(invalidating_changes or [])
        ignored = deepcopy(ignored_changes or [])
        return {
            "surface_kind": "opl_epistemic_review_currentness_evaluation",
            "version": "opl-epistemic-review-currentness-evaluation.v2",
            "scope_id": scope["scope_id"],
            "scope_kind": scope["scope_kind"],
            "status": "stale" if invalidating else "current",
            "invalidating_changes": invalidating,
            "ignored_changes": ignored,
            "reviewed_dependency_refs": epistemic_review_dependency_refs(scope),
            "authority_boundary": deepcopy(scope["authority_boundary"]),
        }

    @classmethod
    def claim_scope(
        cls,
        *,
        sensitivity_only: bool = False,
        supplementary_only: bool = False,
        abstract_headline_allowed: bool = False,
    ) -> dict[str, Any]:
        claim_classes = ["secondary"]
        if sensitivity_only:
            claim_classes.append("sensitivity")
        if supplementary_only:
            claim_classes.append("supplementary_only")
        return {
            "claim_classes": claim_classes,
            "claim_ids": ["bounded_candidate_claim"],
            "permitted_sections": ["supplement" if supplementary_only else "results"],
            "required_disclosures": [
                "report the bounded evidence denominator and uncertainty"
            ],
            "prohibited_claims": ["causal or clinical-quality interpretation"],
            "sensitivity_only": sensitivity_only,
            "supplementary_only": supplementary_only,
            "abstract_headline_allowed": abstract_headline_allowed,
        }

    @classmethod
    def candidate_member(cls) -> dict[str, Any]:
        return {
            "kind": "mas_artifact",
            "role": "candidate_artifact",
            "ref": "mas-artifact://bounded-candidate",
            "size_bytes": 431,
            "sha256": cls.digest("bounded-candidate-bytes"),
        }

    @classmethod
    def evidence_member(cls) -> dict[str, Any]:
        return {
            "kind": "mas_evidence",
            "role": "evidence_record",
            "ref": "mas-evidence://bounded-candidate-evidence",
            "size_bytes": 733,
            "sha256": cls.digest("bounded-candidate-evidence-bytes"),
        }

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

    @classmethod
    def generation_manifest(
        cls,
        scope: str,
        *,
        schema_version: int = 1,
        generation_id: str | None = None,
        artifact_sha_overrides: dict[str, str] | None = None,
        artifact_ref_overrides: dict[str, str] | None = None,
        artifact_member_id_overrides: dict[str, str] | None = None,
        extra_artifacts: list[dict[str, Any]] | None = None,
        professional_skill_invocations: list[dict[str, Any]] | None = None,
        include_professional_skill_invocations: bool = True,
        omit_professional_skill_ids: tuple[str, ...] = (),
        professional_figure_composition_mode: str = "single_canvas_direct",
        include_first_draft_quality_application: bool | None = None,
        first_draft_application_schema_version: int = 2,
        paper_type: str = "prediction_model",
        validation_design: str = "internal_validation",
        reports_fixed_horizon_risk: bool = True,
        competing_risk_relevant: bool = True,
        reports_decision_curve_analysis: bool = True,
        includes_table_one: bool = True,
        requires_reader_pdf: bool = True,
        uses_clinical_or_registry_data: bool = True,
        disposition_overrides: dict[str, dict[str, Any]] | None = None,
        include_clinical_analysis_identity_admission: bool | None = None,
        include_clinical_analysis_identity_artifact: bool | None = None,
        clinical_analysis_identity_status: str = "adjudicator_required",
        include_revision_generation_bindings: bool | None = None,
        dependency_currentness: str = "current",
        reviewer_response_sync_status: str = "synchronized",
        reviewer_response_candidate_state: str = "pre_freeze",
        reviewer_response_item_status: str = "implemented_candidate",
        reviewer_response_post_freeze_disposition: str = "not_started",
        candidate_receipt: dict[str, Any] | None = None,
        review_receipts: list[dict[str, Any]] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        generation_id = generation_id or cls.generation_id
        artifact_sha_overrides = artifact_sha_overrides or {}
        artifact_ref_overrides = artifact_ref_overrides or {}
        artifact_member_id_overrides = artifact_member_id_overrides or {}
        if include_first_draft_quality_application is None:
            include_first_draft_quality_application = (
                schema_version == 2 and scope != "analysis_generation"
            )
        if include_clinical_analysis_identity_admission is None:
            include_clinical_analysis_identity_admission = (
                schema_version == 2 and scope == "analysis_generation"
            )
        if include_clinical_analysis_identity_artifact is None:
            include_clinical_analysis_identity_artifact = (
                include_clinical_analysis_identity_admission
            )
        if include_revision_generation_bindings is None:
            include_revision_generation_bindings = (
                schema_version == 2 and scope != "analysis_generation"
            )
        include_scholar_v2_semantics = (
            include_revision_generation_bindings
            and first_draft_application_schema_version == 2
        )
        applicable_first_draft_fields = {
            "medical_initial_draft_preflight_candidate_ref",
            "citation_source_coverage_ref",
            "claim_guardrail_ref",
        }
        if include_scholar_v2_semantics:
            applicable_first_draft_fields.update(
                {
                    "active_reference_currentness_ref",
                    "author_stance_integrity_ref",
                }
            )
        if uses_clinical_or_registry_data:
            applicable_first_draft_fields.add(
                "clinical_analysis_input_identity_ref"
            )
        if paper_type == "prediction_model":
            applicable_first_draft_fields.update(
                {
                    "validation_partition_integrity_ref",
                    "endpoint_analysis_set_reconciliation_ref",
                    "model_complexity_sparse_event_ref",
                }
            )
            if include_scholar_v2_semantics:
                applicable_first_draft_fields.add(
                    "linked_prediction_performance_ref"
                )
        if reports_fixed_horizon_risk:
            applicable_first_draft_fields.add("fixed_horizon_risk_semantics_ref")
        if competing_risk_relevant:
            applicable_first_draft_fields.add("competing_risk_ref")
        if reports_decision_curve_analysis:
            applicable_first_draft_fields.add("decision_curve_validity_ref")
        if includes_table_one:
            applicable_first_draft_fields.add("baseline_table_traceability_ref")
        if requires_reader_pdf:
            applicable_first_draft_fields.add(
                "document_display_scope_coverage_ref"
            )
            if include_scholar_v2_semantics:
                applicable_first_draft_fields.add("display_render_integrity_ref")
        if validation_design == "external_validation":
            applicable_first_draft_fields.add("external_transportability_ref")
        roles = list(ROLES_BY_SCOPE[scope])
        if include_clinical_analysis_identity_artifact and (
            "clinical_analysis_input_identity" not in roles
        ):
            roles.append("clinical_analysis_input_identity")
        if include_revision_generation_bindings:
            roles.extend(
                role
                for role in (
                    *SELECTED_BUILD_ROLE_BY_REF_FIELD.values(),
                    "reviewer_response",
                    "reviewer_action_matrix",
                    "reviewer_artifact_inventory",
                )
                if role not in roles
            )
            if reviewer_response_post_freeze_disposition in {
                "external_synthesis_bound",
                "scientific_change_requires_new_revision",
            }:
                roles.append("reviewer_external_synthesis")
            if (
                reviewer_response_post_freeze_disposition
                == "scientific_change_requires_new_revision"
            ):
                roles.append("reviewer_new_revision")
        if include_first_draft_quality_application:
            roles.extend(
                FIRST_DRAFT_ROLE_BY_REF_FIELD[field]
                for field in FIRST_DRAFT_ROLE_BY_REF_FIELD
                if field in applicable_first_draft_fields
                and FIRST_DRAFT_ROLE_BY_REF_FIELD[field] not in roles
            )
            if requires_reader_pdf and "pdf" not in roles:
                roles.append("pdf")
        artifacts: list[dict[str, Any]] = []
        for index, role in enumerate(roles):
            if role == "candidate_admission_receipt" and candidate_receipt is not None:
                artifact = {
                    "role": role,
                    "ref": candidate_receipt["receipt_id"],
                    "size_bytes": candidate_receipt["receipt_size_bytes"],
                    "sha256": candidate_receipt["receipt_fingerprint"],
                }
                if schema_version == 2:
                    artifact["member_id"] = artifact_member_id_overrides.get(
                        role, f"mas-member:{role}:primary"
                    )
                artifacts.append(artifact)
                continue
            role_scope = "analysis_generation" if role in ANALYSIS_ROLES else scope
            artifact = {
                "role": role,
                "ref": artifact_ref_overrides.get(
                    role, f"workspace://study/{role_scope}/{role}"
                ),
                "size_bytes": 1000 + index,
                "sha256": artifact_sha_overrides.get(role)
                or cls.digest(
                    f"{generation_id if schema_version == 1 else 'stable'}:"
                    f"{role_scope}:{role}:bytes"
                ),
            }
            if schema_version == 2:
                artifact["member_id"] = artifact_member_id_overrides.get(
                    role, f"mas-member:{role}:primary"
                )
            artifacts.append(artifact)
        if include_revision_generation_bindings:
            root_output = next(
                item for item in artifacts if item["role"] == "root_reader_output"
            )
            selected_output = next(
                item for item in artifacts if item["role"] == "selected_reader_output"
            )
            selected_output["size_bytes"] = root_output["size_bytes"]
            selected_output["sha256"] = root_output["sha256"]
        candidate = cls.candidate_member()
        evidence = cls.evidence_member()
        candidate_artifact = {
            name: value for name, value in candidate.items() if name != "kind"
        }
        evidence_artifact = {
            name: value for name, value in evidence.items() if name != "kind"
        }
        if schema_version == 2:
            candidate_artifact["member_id"] = artifact_member_id_overrides.get(
                "candidate_artifact", "mas-member:candidate_artifact:primary"
            )
            evidence_artifact["member_id"] = artifact_member_id_overrides.get(
                "evidence_record", "mas-member:evidence_record:primary"
            )
        artifacts.extend([candidate_artifact, evidence_artifact])
        artifacts.extend(deepcopy(extra_artifacts or []))
        artifacts.sort(key=lambda item: (item["role"], item["ref"], item["sha256"]))
        core = {
            "surface_kind": "mas_evidence_generation_manifest",
            "schema_version": schema_version,
            "generation_id": generation_id,
            "manifest_scope": scope,
            "artifacts": artifacts,
        }
        if include_first_draft_quality_application:
            core["first_draft_quality_application"] = (
                cls.first_draft_quality_application(
                    artifacts,
                    schema_version=first_draft_application_schema_version,
                    paper_type=paper_type,
                    validation_design=validation_design,
                    reports_fixed_horizon_risk=reports_fixed_horizon_risk,
                    competing_risk_relevant=competing_risk_relevant,
                    reports_decision_curve_analysis=reports_decision_curve_analysis,
                    includes_table_one=includes_table_one,
                    requires_reader_pdf=requires_reader_pdf,
                    uses_clinical_or_registry_data=(
                        uses_clinical_or_registry_data
                    ),
                    include_scholar_v2_semantics=include_scholar_v2_semantics,
                    disposition_overrides=disposition_overrides,
                )
            )
        if schema_version == 2:
            from med_autoscience.authority_handlers._generation_manifest import (
                build_review_scopes,
            )

            core["review_scopes"] = build_review_scopes(artifacts, scope)
            if (
                include_professional_skill_invocations
                and scope != "analysis_generation"
            ):
                generated_invocations = deepcopy(
                    professional_skill_invocations
                    if professional_skill_invocations is not None
                    else [
                        *cls.professional_manuscript_skill_invocations(
                            artifacts,
                            schema_version=(
                                2 if include_first_draft_quality_application else 1
                            ),
                            include_scholar_v2_semantics=(
                                include_scholar_v2_semantics
                            ),
                        ),
                        *cls.professional_figure_skill_invocations(
                            artifacts,
                            composition_mode=professional_figure_composition_mode,
                            schema_version=(
                                2 if include_first_draft_quality_application else 1
                            ),
                        ),
                    ]
                )
                if (
                    "first_draft_quality_application" in core
                    and core["first_draft_quality_application"]["schema_version"] == 2
                    and include_scholar_v2_semantics
                ):
                    core["first_draft_quality_application"][
                        "scholar_v2_semantic_policy_bindings"
                    ] = cls.scholar_v2_semantic_policy_bindings(
                        generated_invocations,
                        core["first_draft_quality_application"]["candidate_refs"],
                    )
                generated_invocations = [
                    item
                    for item in generated_invocations
                    if item["skill_id"] not in set(omit_professional_skill_ids)
                ]
                generated_invocations.sort(
                    key=lambda item: (
                        item["surface_kind"],
                        item.get("figure_id", ""),
                        item["skill_id"],
                    )
                )
                core["professional_skill_invocations"] = generated_invocations
            if include_clinical_analysis_identity_admission:
                identity = next(
                    item
                    for item in artifacts
                    if item["role"] == "clinical_analysis_input_identity"
                )
                route_state = clinical_analysis_identity_status != "adjudicator_required"
                human_gate = clinical_analysis_identity_status == "open_human_gate"
                core["clinical_analysis_identity_admission"] = {
                    "surface_kind": "mas_clinical_analysis_identity_admission",
                    "schema_version": 1,
                    "status": clinical_analysis_identity_status,
                    "clinical_analysis_input_identity_ref": cls.artifact_exact_ref(
                        identity
                    ),
                    "reason_codes": (
                        ["clinical_analysis_identity_unresolved"] if route_state else []
                    ),
                    "unresolved_items": (
                        ["resolve the clinical analysis input identity"]
                        if route_state
                        else []
                    ),
                    "next_owner": (
                        "human_principal_investigator"
                        if human_gate
                        else (
                            "baseline_and_evidence_setup" if route_state else None
                        )
                    ),
                    "human_gate_refs": (
                        [cls.typed_ref("mas_human_gate", "clinical-identity")]
                        if human_gate
                        else []
                    ),
                    "authority_boundary": cls.no_authority_boundary(),
                }
            if include_revision_generation_bindings:
                artifact_by_role = {item["role"]: item for item in artifacts}
                dependency_manifest_ref = cls.artifact_exact_ref(
                    artifact_by_role["build_dependency_manifest"]
                )
                response_ref = cls.artifact_exact_ref(
                    artifact_by_role["reviewer_response"]
                )
                external_synthesis_ref = (
                    cls.artifact_exact_ref(
                        artifact_by_role["reviewer_external_synthesis"]
                    )
                    if "reviewer_external_synthesis" in artifact_by_role
                    else None
                )
                new_revision_ref = (
                    cls.artifact_exact_ref(artifact_by_role["reviewer_new_revision"])
                    if "reviewer_new_revision" in artifact_by_role
                    else None
                )
                reviewer_response_currentness = {
                    "generation_id": generation_id,
                    "candidate_state": reviewer_response_candidate_state,
                    "response_ref": response_ref,
                    "prior_frozen_response_ref": (
                        deepcopy(response_ref)
                        if reviewer_response_candidate_state == "frozen"
                        else None
                    ),
                    "post_freeze_disposition": (
                        reviewer_response_post_freeze_disposition
                    ),
                    "external_synthesis_ref": external_synthesis_ref,
                    "new_revision_ref": new_revision_ref,
                    "owner_ledger_history_ref": cls.exact_ref(
                        "opl_action_output",
                        "build-dependency-currentness-owner-ledger",
                    ),
                }
                dependency_currentness_authority = (
                    cls.build_dependency_currentness_authority(
                        dependency_manifest_ref,
                        dependency_currentness,
                        reviewer_response_currentness,
                    )
                )
                dependency_currentness_receipt = cls.seal(
                    {
                        "receipt_kind": "mas_build_dependency_currentness_receipt",
                        "schema_version": 1,
                        "owner": "MedAutoScience",
                        "authority_role": "build_dependency_currentness_owner",
                        "authority_ref": dependency_currentness_authority[
                            "authority_ref"
                        ],
                        "dependency_manifest_ref": dependency_manifest_ref,
                        "dependency_currentness": dependency_currentness,
                    },
                    "mas-build-dependency-currentness",
                )
                core["selected_build_binding"] = {
                    "surface_kind": "mas_selected_build_binding",
                    "schema_version": 1,
                    "selected_archive_label": "current-candidate",
                    **{
                        ref_field: cls.artifact_exact_ref(artifact_by_role[role])
                        for ref_field, role in SELECTED_BUILD_ROLE_BY_REF_FIELD.items()
                    },
                    "dependency_currentness": dependency_currentness,
                    "dependency_currentness_receipt_ref": cls.receipt_ref(
                        "mas_build_dependency_currentness_receipt",
                        dependency_currentness_receipt,
                    ),
                    "dependency_currentness_receipt": dependency_currentness_receipt,
                    "root_matches_selected_bytes": True,
                    "authority_boundary": cls.no_authority_boundary(),
                }
                manuscript = artifact_by_role["canonical_manuscript"]
                core["reviewer_response_sync"] = {
                    "surface_kind": "mas_reviewer_response_sync",
                    "schema_version": 1,
                    "response_ref": response_ref,
                    "action_matrix_ref": cls.artifact_exact_ref(
                        artifact_by_role["reviewer_action_matrix"]
                    ),
                    "action_matrix_item_ids": ["REV-001"],
                    "artifact_inventory_ref": cls.artifact_exact_ref(
                        artifact_by_role["reviewer_artifact_inventory"]
                    ),
                    "candidate_state": reviewer_response_candidate_state,
                    "sync_status": reviewer_response_sync_status,
                    "items": [
                        {
                            "comment_id": "REV-001",
                            "status": reviewer_response_item_status,
                            "affected_artifact_bindings": [
                                cls.affected_artifact_binding(manuscript)
                            ],
                            "evidence_refs": [
                                cls.exact_ref("mas_evidence", "revision-response")
                            ],
                            "remaining_gap_or_not_applicable_reason": None,
                        }
                    ],
                    "external_synthesis_ref": external_synthesis_ref,
                    "new_revision_ref": new_revision_ref,
                    "post_freeze_disposition": (
                        reviewer_response_post_freeze_disposition
                    ),
                    "authority_boundary": cls.no_authority_boundary(),
                }
        manifest_sha256 = cls.fingerprint(core)
        manifest = {
            **core,
            "generation_manifest_sha256": manifest_sha256,
            "independent_review_receipts": deepcopy(review_receipts or []),
        }
        manifest_ref = {
            "kind": "mas_generation_manifest",
            "ref": (
                f"mas-generation-manifest:{generation_id}:{scope}:"
                f"{manifest_sha256.removeprefix('sha256:')}"
            ),
            "size_bytes": len(cls.canonical_bytes(core)),
            "sha256": manifest_sha256,
        }
        return manifest, manifest_ref

    @classmethod
    def candidate_request(
        cls,
        *,
        verdict: str = "accepted",
        request_name: str = "candidate-request-current",
        current_request_name: str | None = None,
        superseded_request_names: tuple[str, ...] = (),
        sensitivity_only: bool = False,
        abstract_headline_allowed: bool = False,
        manifest_version: int = 1,
        generation_id: str | None = None,
        include_clinical_analysis_identity_admission: bool | None = None,
        include_clinical_analysis_identity_artifact: bool | None = None,
        clinical_analysis_identity_status: str = "adjudicator_required",
    ) -> dict[str, Any]:
        generation_id = generation_id or cls.generation_id
        manifest, manifest_ref = cls.generation_manifest(
            "analysis_generation",
            schema_version=manifest_version,
            generation_id=generation_id,
            include_clinical_analysis_identity_admission=(
                include_clinical_analysis_identity_admission
            ),
            include_clinical_analysis_identity_artifact=(
                include_clinical_analysis_identity_artifact
            ),
            clinical_analysis_identity_status=clinical_analysis_identity_status,
        )
        candidate = {
            "candidate_id": "bounded-candidate",
            "candidate_member": cls.candidate_member(),
            "evidence_members": [cls.evidence_member()],
            "claim_scope": cls.claim_scope(
                sensitivity_only=sensitivity_only,
                abstract_headline_allowed=abstract_headline_allowed,
            ),
        }
        producer_attempt = cls.typed_ref("opl_stage_attempt", "candidate-producer")
        adjudicator_attempt = cls.typed_ref(
            "opl_stage_attempt", "independent-medical-adjudicator"
        )
        candidate_packet = cls.exact_ref("opl_action_output", "candidate-source-packet")
        admission_request = cls.exact_ref("opl_action_output", request_name)
        current_admission_request = cls.exact_ref(
            "opl_action_output", current_request_name or request_name
        )
        superseded_requests = [
            cls.exact_ref("opl_action_output", name)
            for name in superseded_request_names
        ]
        decision_code = {
            "accepted": (
                "accepted_for_bounded_sensitivity_use"
                if sensitivity_only
                else "accepted_for_exact_claim_scope"
            ),
            "rejected": "rejected_unsupported_evidence",
            "route_back": "claim_scope_revision_required",
            "waived": "waived_with_typed_scope",
        }[verdict]
        next_owner = "candidate_evidence_owner" if verdict == "route_back" else None
        resume_condition = (
            "supply a revised exact claim scope" if verdict == "route_back" else None
        )
        waiver = None
        if verdict == "waived":
            waiver = {
                "waiver_kind": "mas_candidate_admission_waiver",
                "waiver_code": "waived_non_material_candidate_gap",
                "scope": "candidate_record_only",
                "evidence_refs": [cls.typed_ref("mas_evidence", "waiver-evidence")],
                "expires_on_generation_change": True,
                "authorizes_manuscript_consumption": False,
            }
        candidate_ref = {
            name: value
            for name, value in candidate["candidate_member"].items()
            if name != "role"
        }
        evidence_refs = [
            {name: value for name, value in item.items() if name != "role"}
            for item in candidate["evidence_members"]
        ]
        adjudicator_core = {
            "receipt_kind": "mas_candidate_adjudicator_receipt",
            "schema_version": 1,
            "owner": "MedAutoScience",
            "authority_role": "independent_medical_adjudicator",
            "authority_epoch": cls.authority_epoch,
            "producer_attempt_ref": producer_attempt,
            "adjudicator_attempt_ref": adjudicator_attempt,
            "candidate_packet_ref": candidate_packet,
            "admission_request_ref": admission_request,
            "generation_id": generation_id,
            "generation_manifest_ref": manifest_ref,
            "candidate_id": candidate["candidate_id"],
            "candidate_ref": candidate_ref,
            "evidence_refs": evidence_refs,
            "claim_scope": candidate["claim_scope"],
            "candidate_record_sha256": cls.fingerprint(candidate),
            "verdict": verdict,
            "decision_code": decision_code,
            "next_owner": next_owner,
            "resume_condition": resume_condition,
            "waiver": waiver,
        }
        adjudicator_receipt = cls.seal(adjudicator_core, "mas-candidate-adjudicator")
        adjudicator_ref = cls.receipt_ref(
            "mas_candidate_adjudicator_receipt", adjudicator_receipt
        )
        currentness_core = {
            "receipt_kind": "mas_generation_currentness_receipt",
            "schema_version": 1,
            "owner": "MedAutoScience",
            "authority_role": "generation_currentness_owner",
            "authority_epoch": cls.authority_epoch,
            "current_generation_id": generation_id,
            "current_generation_manifest_ref": manifest_ref,
            "current_admission_request_ref": current_admission_request,
            "current_adjudicator_receipt_ref": adjudicator_ref,
            "superseded_generation_ids": [],
            "superseded_request_refs": superseded_requests,
        }
        currentness_receipt = cls.seal(currentness_core, "mas-generation-currentness")
        currentness_ref = cls.receipt_ref(
            "mas_generation_currentness_receipt", currentness_receipt
        )
        return {
            "surface_kind": "mas_candidate_admission_authority_request",
            "schema_version": 2,
            "adjudicator_context": {
                "producer_attempt_ref": producer_attempt,
                "adjudicator_attempt_ref": adjudicator_attempt,
                "candidate_packet_ref": candidate_packet,
                "admission_request_ref": admission_request,
                "adjudicator_receipt_ref": adjudicator_ref,
                "currentness_receipt_ref": currentness_ref,
            },
            "mission": {
                "program_id": "program-dm",
                "study_id": "study-003",
                "mission_id": "paper-mission-study-003",
                "stage_id": "manuscript_authoring",
                "stage_goal_ref": cls.typed_ref(
                    "mas_stage_goal", "manuscript-authoring"
                ),
            },
            "generation_manifest": manifest,
            "generation_manifest_ref": manifest_ref,
            "currentness_receipt": currentness_receipt,
            "candidate": candidate,
            "adjudicator_receipt": adjudicator_receipt,
            "hard_gate": {
                "kind": "none",
                "reason_code": None,
                "evidence_refs": [],
                "next_owner": None,
                "resume_condition": None,
            },
        }

    @classmethod
    def independent_review_wrapper(
        cls,
        *,
        lane: str,
        manifest: dict[str, Any],
        manifest_ref: dict[str, Any],
        candidate_receipt_ref: dict[str, Any],
        review_request_ref: dict[str, Any],
        producer_output_ref: dict[str, Any],
        verdict: str = "passed",
        defect_refs: list[dict[str, Any]] | None = None,
        quality_debt_codes: list[str] | None = None,
    ) -> dict[str, Any]:
        scope = next(
            (
                item
                for item in manifest.get("review_scopes", [])
                if item["review_lane"] == lane
            ),
            None,
        )
        core = {
            "receipt_kind": "mas_independent_review_receipt",
            "schema_version": manifest["schema_version"],
            "issuer": "MedAutoScience",
            "authority_role": AUTHORITY_ROLE_BY_LANE[lane],
            "authority_epoch": cls.authority_epoch,
            "review_lane": lane,
            "verdict": verdict,
            "review_request_ref": review_request_ref,
            "producer_output_ref": producer_output_ref,
            "reviewer_attempt_ref": cls.typed_ref(
                "opl_stage_attempt", f"independent-{lane}-reviewer"
            ),
            "rubric_ref": cls.typed_ref("mas_quality_rubric", f"{lane}-rubric"),
            "accepted_candidate_receipt_refs": [candidate_receipt_ref],
            "defect_refs": deepcopy(defect_refs or []),
            "quality_debt_codes": list(quality_debt_codes or []),
        }
        if manifest["schema_version"] == 1:
            core.update(
                {
                    "generation_id": manifest["generation_id"],
                    "generation_manifest_sha256": manifest[
                        "generation_manifest_sha256"
                    ],
                    "reviewed_members": deepcopy(manifest["artifacts"]),
                }
            )
        else:
            if scope is None:
                raise AssertionError(f"missing review scope for {lane}")
            from med_autoscience.authority_handlers._generation_manifest import (
                review_scope_member_projection,
            )

            binding_members = review_scope_member_projection(scope["reviewed_members"])
            owner_refs_by_member_id = {
                item["member_id"]: item["ref"] for item in scope["reviewed_members"]
            }
            authority_issuer = cls.review_snapshot_authority_issuer()
            authority_record = {
                "surface_kind": "mas_review_input_snapshot_authority",
                "schema_version": 2,
                "issuer": authority_issuer,
                "generation_ref": manifest_ref["ref"],
                "review_lane": lane,
                "scope_policy_id": "mas_review_scope_dependency_map",
                "scope_policy_version": 2,
                "review_scope_sha256": scope["review_scope_sha256"],
                "members": [
                    {
                        **item,
                        "owner_ref": owner_refs_by_member_id[item["member_id"]],
                    }
                    for item in binding_members
                ],
            }
            authority_sha256 = cls.fingerprint(authority_record)
            core.update(
                {
                    "issued_generation_id": manifest["generation_id"],
                    "issued_generation_manifest_sha256": manifest[
                        "generation_manifest_sha256"
                    ],
                    "scope_policy_id": scope["scope_policy_id"],
                    "scope_policy_version": scope["scope_policy_version"],
                    "review_scope_sha256": scope["review_scope_sha256"],
                    "reviewed_members": deepcopy(scope["reviewed_members"]),
                    "review_input_snapshot_binding": {
                        "surface_kind": "opl_reviewer_input_snapshot_binding",
                        "schema_version": 3,
                        "snapshot_manifest_ref": cls.exact_ref(
                            "opl_reviewer_input_snapshot_manifest",
                            f"{manifest['generation_id']}-{lane}-review-input-snapshot",
                        ),
                        "owner_authority_ref": {
                            "kind": "mas_review_input_snapshot_authority",
                            "ref": (
                                "mas-review-input-snapshot-authority:"
                                f"{authority_sha256.removeprefix('sha256:')}"
                            ),
                            "size_bytes": len(cls.canonical_bytes(authority_record)),
                            "sha256": authority_sha256,
                        },
                        "producer_attempt_ref": authority_issuer["stage_attempt_ref"],
                        "execution_content_binding_sha256": authority_issuer[
                            "execution_content_binding_sha256"
                        ],
                    },
                }
            )
        receipt_fingerprint = cls.fingerprint(core)
        receipt_ref = {
            "kind": "mas_reviewer_receipt",
            "ref": (
                f"mas-independent-review-receipt:{lane}:"
                f"{receipt_fingerprint.removeprefix('sha256:')}"
            ),
            "size_bytes": len(cls.canonical_bytes(core)),
            "sha256": receipt_fingerprint,
        }
        return {"receipt_ref": receipt_ref, "receipt": core}

    @classmethod
    def paper_request(
        cls,
        *,
        scope: str = "manuscript_generation",
        stage_id: str = "manuscript_authoring",
        candidate_verdict: str = "accepted",
        candidate_sensitivity_only: bool = False,
        supplied_review_request_name: str = "review-request-current",
        current_review_request_name: str | None = None,
        superseded_review_request_names: tuple[str, ...] = (),
        review_verdicts: dict[str, str] | None = None,
        manifest_version: int = 2,
        generation_id: str | None = None,
        artifact_sha_overrides: dict[str, str] | None = None,
        artifact_ref_overrides: dict[str, str] | None = None,
        artifact_member_id_overrides: dict[str, str] | None = None,
        extra_artifacts: list[dict[str, Any]] | None = None,
        professional_skill_invocations: list[dict[str, Any]] | None = None,
        include_professional_skill_invocations: bool = True,
        omit_professional_skill_ids: tuple[str, ...] = (),
        professional_figure_composition_mode: str = "single_canvas_direct",
        include_first_draft_quality_application: bool | None = None,
        first_draft_application_schema_version: int = 2,
        paper_type: str = "prediction_model",
        validation_design: str = "internal_validation",
        reports_fixed_horizon_risk: bool = True,
        competing_risk_relevant: bool = True,
        reports_decision_curve_analysis: bool = True,
        includes_table_one: bool = True,
        requires_reader_pdf: bool = True,
        uses_clinical_or_registry_data: bool = True,
        disposition_overrides: dict[str, dict[str, Any]] | None = None,
        include_revision_generation_bindings: bool | None = None,
        dependency_currentness: str = "current",
        reviewer_response_sync_status: str = "synchronized",
        reviewer_response_candidate_state: str = "pre_freeze",
        reviewer_response_item_status: str = "implemented_candidate",
        reviewer_response_post_freeze_disposition: str = "not_started",
    ) -> dict[str, Any]:
        from med_autoscience.authority_handlers.candidate_admission import (
            evaluate_candidate_admission_authority,
        )

        candidate_request = cls.candidate_request(
            verdict=candidate_verdict,
            sensitivity_only=candidate_sensitivity_only,
            manifest_version=manifest_version,
            generation_id=generation_id,
        )
        candidate_result = evaluate_candidate_admission_authority(candidate_request)
        if candidate_result["status"] not in {"accepted", "rejected"}:
            raise AssertionError(candidate_result)
        candidate_receipt = candidate_result["disposition_receipt"]
        candidate_receipt_ref = cls.receipt_ref(
            "mas_candidate_admission_receipt", candidate_receipt
        )
        manifest, manifest_ref = cls.generation_manifest(
            scope,
            schema_version=manifest_version,
            generation_id=generation_id,
            artifact_sha_overrides=artifact_sha_overrides,
            artifact_ref_overrides=artifact_ref_overrides,
            artifact_member_id_overrides=artifact_member_id_overrides,
            extra_artifacts=extra_artifacts,
            candidate_receipt=candidate_receipt,
            professional_skill_invocations=professional_skill_invocations,
            include_professional_skill_invocations=(
                include_professional_skill_invocations
            ),
            omit_professional_skill_ids=omit_professional_skill_ids,
            professional_figure_composition_mode=(professional_figure_composition_mode),
            include_first_draft_quality_application=(
                include_first_draft_quality_application
            ),
            first_draft_application_schema_version=(
                first_draft_application_schema_version
            ),
            paper_type=paper_type,
            validation_design=validation_design,
            reports_fixed_horizon_risk=reports_fixed_horizon_risk,
            competing_risk_relevant=competing_risk_relevant,
            reports_decision_curve_analysis=reports_decision_curve_analysis,
            includes_table_one=includes_table_one,
            requires_reader_pdf=requires_reader_pdf,
            uses_clinical_or_registry_data=uses_clinical_or_registry_data,
            disposition_overrides=disposition_overrides,
            include_revision_generation_bindings=include_revision_generation_bindings,
            dependency_currentness=dependency_currentness,
            reviewer_response_sync_status=reviewer_response_sync_status,
            reviewer_response_candidate_state=reviewer_response_candidate_state,
            reviewer_response_item_status=reviewer_response_item_status,
            reviewer_response_post_freeze_disposition=(
                reviewer_response_post_freeze_disposition
            ),
        )
        producer_output_ref = cls.exact_ref(
            "opl_action_output", f"paper-output-{scope}"
        )
        supplied_review_request = cls.exact_ref(
            "opl_action_output", supplied_review_request_name
        )
        current_review_request = cls.exact_ref(
            "opl_action_output",
            current_review_request_name or supplied_review_request_name,
        )
        wrappers = [
            cls.independent_review_wrapper(
                lane=lane,
                manifest=manifest,
                manifest_ref=manifest_ref,
                candidate_receipt_ref=candidate_receipt_ref,
                review_request_ref=supplied_review_request,
                producer_output_ref=producer_output_ref,
                verdict=(review_verdicts or {}).get(lane, "passed"),
                defect_refs=(
                    [cls.typed_ref("mas_review_defect", f"{lane}-defect")]
                    if (review_verdicts or {}).get(lane) == "revision_required"
                    else []
                ),
            )
            for lane in LANES_BY_SCOPE[scope]
        ]
        manifest["independent_review_receipts"] = wrappers
        selected_build_currentness_authority = None
        if "selected_build_binding" in manifest:
            response_sync = manifest["reviewer_response_sync"]
            response_ref = deepcopy(response_sync["response_ref"])
            selected_build_currentness_authority = (
                cls.build_dependency_currentness_authority(
                    manifest["selected_build_binding"]["dependency_manifest_ref"],
                    manifest["selected_build_binding"]["dependency_currentness"],
                    {
                        "generation_id": manifest["generation_id"],
                        "candidate_state": response_sync["candidate_state"],
                        "response_ref": response_ref,
                        "prior_frozen_response_ref": (
                            deepcopy(response_ref)
                            if response_sync["candidate_state"] == "frozen"
                            else None
                        ),
                        "post_freeze_disposition": response_sync[
                            "post_freeze_disposition"
                        ],
                        "external_synthesis_ref": deepcopy(
                            response_sync["external_synthesis_ref"]
                        ),
                        "new_revision_ref": deepcopy(
                            response_sync["new_revision_ref"]
                        ),
                        "owner_ledger_history_ref": cls.exact_ref(
                            "opl_action_output",
                            "build-dependency-currentness-owner-ledger",
                        ),
                    },
                )
            )
        superseded_review_requests = [
            cls.exact_ref("opl_action_output", name)
            for name in superseded_review_request_names
        ]
        currentness_core: dict[str, Any] = {
            "receipt_kind": "mas_review_currentness_receipt",
            "schema_version": manifest_version,
            "owner": "MedAutoScience",
            "authority_role": "review_currentness_owner",
            "authority_epoch": cls.authority_epoch,
            "current_generation_id": manifest["generation_id"],
            "current_generation_manifest_ref": manifest_ref,
            "current_review_request_ref": current_review_request,
            "current_candidate_admission_receipt_refs": [candidate_receipt_ref],
        }
        if manifest_version == 1:
            currentness_core.update(
                {
                    "current_review_receipt_refs": [
                        deepcopy(wrapper["receipt_ref"]) for wrapper in wrappers
                    ],
                    "superseded_generation_ids": [],
                    "superseded_review_request_refs": superseded_review_requests,
                }
            )
        else:
            currentness_core["current_build_dependency_authority_refs"] = (
                [
                    deepcopy(
                        selected_build_currentness_authority["authority_ref"]
                    )
                ]
                if selected_build_currentness_authority is not None
                else []
            )
            currentness_core["lane_currentness"] = [
                {
                    "review_lane": wrapper["receipt"]["review_lane"],
                    "review_authority_epoch": wrapper["receipt"]["authority_epoch"],
                    "currentness_status": "fresh",
                    "current_rubric_ref": deepcopy(wrapper["receipt"]["rubric_ref"]),
                    "review_scope_sha256": wrapper["receipt"]["review_scope_sha256"],
                    "review_receipt_issued_generation_id": wrapper["receipt"][
                        "issued_generation_id"
                    ],
                    "review_receipt_issued_generation_manifest_sha256": wrapper[
                        "receipt"
                    ]["issued_generation_manifest_sha256"],
                    "current_review_request_ref": deepcopy(
                        wrapper["receipt"]["review_request_ref"]
                    ),
                    "current_review_receipt_ref": deepcopy(wrapper["receipt_ref"]),
                    "superseded_review_request_refs": [],
                    "reuse_provenance": None,
                    "epistemic_currentness": cls.epistemic_currentness(
                        manifest,
                        wrapper["receipt"]["review_lane"],
                    ),
                }
                for wrapper in wrappers
            ]
            currentness_core["lane_currentness"].sort(
                key=lambda item: item["review_lane"]
            )
        currentness_receipt = cls.seal(currentness_core, "mas-review-currentness")
        currentness_ref = cls.receipt_ref(
            "mas_review_currentness_receipt", currentness_receipt
        )
        candidate_ref = candidate_receipt["candidate_ref"]
        evidence_ref = candidate_receipt["evidence_refs"][0]
        producer_attempt_ref = cls.typed_ref("opl_stage_attempt", "paper-producer")
        mission_identity = {
            "program_id": "program-dm",
            "study_id": "study-003",
            "mission_id": "paper-mission-study-003",
        }
        revision_core = {
            "receipt_kind": "mas_revision_consumption_receipt",
            "schema_version": 1,
            "owner": "MedAutoScience",
            "authority_role": "revision_consumption_owner",
            "mission_identity": mission_identity,
            "generation_id": manifest["generation_id"],
            "producer_attempt_ref": producer_attempt_ref,
            "producer_output_ref": producer_output_ref,
            "applicability": "not_applicable",
            "revision_intake_refs": [],
            "opl_review_receipt_ref": None,
            "opl_finding_lineage": None,
            "finding_closures": [],
            "consumed_revision_refs": [],
            "authority_boundary": {
                "receipt_can_authorize_review_verdict": False,
                "receipt_can_authorize_owner_receipt": False,
                "receipt_can_authorize_publication": False,
                "receipt_can_authorize_submission": False,
                "receipt_can_create_typed_blocker": False,
            },
        }
        revision_receipt = cls.seal(revision_core, "mas-revision-consumption")
        revision_consumption = {
            "surface_kind": "mas_revision_consumption_binding",
            "schema_version": 1,
            "current_accepted_or_active_revision_intake_refs": [],
            "consumption_receipt_ref": cls.receipt_ref(
                "mas_revision_consumption_receipt", revision_receipt
            ),
            "consumption_receipt": revision_receipt,
        }
        request = {
            "surface_kind": "mas_paper_mission_authority_request",
            "schema_version": 2,
            "host_context": {
                "action_id": "paper_mission",
                "run_ref": cls.typed_ref("opl_stage_run", "paper-run"),
                "producer_attempt_ref": producer_attempt_ref,
                "output_ref": producer_output_ref,
                "output_state": "consumable",
            },
            "mission": {
                **mission_identity,
                "stage_id": stage_id,
                "stage_goal_ref": cls.typed_ref("mas_stage_goal", stage_id),
            },
            "medical_evidence": {
                "source_readiness_status": "ready",
                "source_readiness_receipt_ref": cls.typed_ref(
                    "mas_source_readiness_receipt", "source-ready"
                ),
                "claim_evidence_status": "aligned",
                "claim_boundary_ref": cls.typed_ref(
                    "mas_claim_boundary", "bounded-claims"
                ),
                "candidate_artifact_refs": [
                    {
                        "kind": candidate_ref["kind"],
                        "ref": candidate_ref["ref"],
                        "sha256": candidate_ref["sha256"],
                    }
                ],
                "evidence_refs": [
                    {
                        "kind": evidence_ref["kind"],
                        "ref": evidence_ref["ref"],
                        "sha256": evidence_ref["sha256"],
                    }
                ],
                "negative_result_refs": [],
                "failed_path_refs": [],
                "artifact_lineage_refs": [
                    cls.typed_ref("mas_artifact_lineage", "paper-lineage")
                ],
                "reproducibility_refs": [
                    cls.typed_ref("mas_reproducibility", "paper-reproducibility")
                ],
            },
            "generation_manifest": manifest,
            "generation_manifest_ref": manifest_ref,
            "candidate_admissions": [
                {
                    "receipt_ref": candidate_receipt_ref,
                    "receipt": candidate_receipt,
                }
            ],
            "review_authority": {
                "review_request_ref": supplied_review_request,
                "currentness_receipt_ref": currentness_ref,
                "currentness_receipt": currentness_receipt,
            },
            "revision_consumption": revision_consumption,
            "repair_state": {
                "status": "not_required",
                "attempts_used": 0,
                "max_attempts": 3,
                "repair_attempt_refs": [],
                "latest_repair_output_ref": None,
            },
            "hard_gate": {
                "kind": "none",
                "reason_code": None,
                "evidence_refs": [],
                "next_owner": None,
                "resume_condition": None,
            },
        }
        if selected_build_currentness_authority is not None:
            request["selected_build_currentness_authority"] = (
                selected_build_currentness_authority
            )
            request["host_context"][
                "build_dependency_currentness_authority_ref"
            ] = deepcopy(selected_build_currentness_authority["authority_ref"])
            request["host_context"][
                "build_dependency_currentness_authority_issuer_attempt_ref"
            ] = deepcopy(
                selected_build_currentness_authority["authority_record"][
                    "issuer_attempt_ref"
                ]
            )
        return request

    @classmethod
    def bind_revision_consumption(
        cls,
        request: dict[str, Any],
        *,
        finding_statuses: dict[str, str] | None = None,
        revision_intake_names: tuple[str, ...] = ("revision-intake-current",),
    ) -> None:
        finding_statuses = finding_statuses or {"OPL-REV-001": "closed"}
        revision_intake_refs = [
            cls.exact_ref("opl_revision_intake", name) for name in revision_intake_names
        ]
        revision_intake_refs.sort(
            key=lambda item: (item["ref"], item["size_bytes"], item["sha256"])
        )
        opl_review_receipt_ref = cls.exact_ref(
            "opl_stage_review_receipt", "revision-review-current"
        )
        finding_ids = sorted(finding_statuses)
        finding_lineage = {
            "review_kind": "finding_closure_review",
            "finding_ids": finding_ids,
            "findings_sha256": cls.digest("revision-findings-current"),
            "repair_map_sha256": cls.digest("revision-repair-map-current"),
            "re_review_result_sha256": cls.digest("revision-re-review-current"),
        }
        finding_closures = [
            {
                "finding_id": finding_id,
                "status": status,
                "evidence_refs": [f"mas-revision-evidence://{finding_id}"],
            }
            for finding_id, status in sorted(finding_statuses.items())
        ]
        consumed_revision_refs = [*revision_intake_refs, opl_review_receipt_ref]
        consumed_revision_refs.sort(
            key=lambda item: (
                item["kind"],
                item["ref"],
                item["size_bytes"],
                item["sha256"],
            )
        )
        revision_core = {
            "receipt_kind": "mas_revision_consumption_receipt",
            "schema_version": 1,
            "owner": "MedAutoScience",
            "authority_role": "revision_consumption_owner",
            "mission_identity": {
                name: request["mission"][name]
                for name in ("program_id", "study_id", "mission_id")
            },
            "generation_id": request["generation_manifest"]["generation_id"],
            "producer_attempt_ref": deepcopy(
                request["host_context"]["producer_attempt_ref"]
            ),
            "producer_output_ref": deepcopy(request["host_context"]["output_ref"]),
            "applicability": "revision_consumed",
            "revision_intake_refs": revision_intake_refs,
            "opl_review_receipt_ref": opl_review_receipt_ref,
            "opl_finding_lineage": finding_lineage,
            "finding_closures": finding_closures,
            "consumed_revision_refs": consumed_revision_refs,
            "authority_boundary": {
                "receipt_can_authorize_review_verdict": False,
                "receipt_can_authorize_owner_receipt": False,
                "receipt_can_authorize_publication": False,
                "receipt_can_authorize_submission": False,
                "receipt_can_create_typed_blocker": False,
            },
        }
        revision_receipt = cls.seal(revision_core, "mas-revision-consumption")
        request["revision_consumption"] = {
            "surface_kind": "mas_revision_consumption_binding",
            "schema_version": 1,
            "current_accepted_or_active_revision_intake_refs": deepcopy(
                revision_intake_refs
            ),
            "consumption_receipt_ref": cls.receipt_ref(
                "mas_revision_consumption_receipt", revision_receipt
            ),
            "consumption_receipt": revision_receipt,
        }

    @classmethod
    def reseal_revision_consumption(cls, request: dict[str, Any]) -> None:
        receipt = request["revision_consumption"]["consumption_receipt"]
        core = {
            name: deepcopy(value)
            for name, value in receipt.items()
            if name not in {"receipt_id", "receipt_size_bytes", "receipt_fingerprint"}
        }
        sealed = cls.seal(core, "mas-revision-consumption")
        request["revision_consumption"]["consumption_receipt"] = sealed
        request["revision_consumption"]["consumption_receipt_ref"] = cls.receipt_ref(
            "mas_revision_consumption_receipt", sealed
        )

    @classmethod
    def reseal_review_currentness(cls, request: dict[str, Any]) -> None:
        receipt = request["review_authority"]["currentness_receipt"]
        if receipt["schema_version"] == 2:
            receipt["lane_currentness"].sort(key=lambda item: item["review_lane"])
        core = {
            name: deepcopy(value)
            for name, value in receipt.items()
            if name not in {"receipt_id", "receipt_size_bytes", "receipt_fingerprint"}
        }
        sealed = cls.seal(core, "mas-review-currentness")
        request["review_authority"]["currentness_receipt"] = sealed
        request["review_authority"]["currentness_receipt_ref"] = cls.receipt_ref(
            "mas_review_currentness_receipt", sealed
        )

    @classmethod
    def reseal_selected_build_currentness_receipt(
        cls,
        request: dict[str, Any],
    ) -> None:
        selected_build = request["generation_manifest"]["selected_build_binding"]
        receipt = selected_build["dependency_currentness_receipt"]
        core = {
            name: deepcopy(value)
            for name, value in receipt.items()
            if name not in {"receipt_id", "receipt_size_bytes", "receipt_fingerprint"}
        }
        sealed = cls.seal(core, "mas-build-dependency-currentness")
        selected_build["dependency_currentness_receipt"] = sealed
        selected_build["dependency_currentness_receipt_ref"] = cls.receipt_ref(
            "mas_build_dependency_currentness_receipt", sealed
        )

    @classmethod
    def reseal_selected_build_currentness_authority(
        cls,
        request: dict[str, Any],
    ) -> None:
        authority = request["selected_build_currentness_authority"]
        record = authority["authority_record"]
        authority_sha256 = cls.fingerprint(record)
        authority_ref = {
            "kind": "mas_build_dependency_currentness_authority",
            "ref": (
                "mas-build-dependency-currentness-authority:"
                f"{authority_sha256.removeprefix('sha256:')}"
            ),
            "size_bytes": len(cls.canonical_bytes(record)),
            "sha256": authority_sha256,
        }
        authority["authority_ref"] = authority_ref
        request["review_authority"]["currentness_receipt"][
            "current_build_dependency_authority_refs"
        ] = [deepcopy(authority_ref)]
        request["generation_manifest"]["selected_build_binding"][
            "dependency_currentness_receipt"
        ]["authority_ref"] = deepcopy(authority_ref)
        cls.reseal_selected_build_currentness_receipt(request)
        cls.refresh_paper_manifest_identity(request)

    @classmethod
    def reseal_review_wrapper(cls, wrapper: dict[str, Any]) -> None:
        core = deepcopy(wrapper["receipt"])
        receipt_fingerprint = cls.fingerprint(core)
        lane = core["review_lane"]
        wrapper["receipt_ref"] = {
            "kind": "mas_reviewer_receipt",
            "ref": (
                f"mas-independent-review-receipt:{lane}:"
                f"{receipt_fingerprint.removeprefix('sha256:')}"
            ),
            "size_bytes": len(cls.canonical_bytes(core)),
            "sha256": receipt_fingerprint,
        }

    @classmethod
    def refresh_paper_manifest_identity(cls, request: dict[str, Any]) -> None:
        manifest = request["generation_manifest"]
        manifest["artifacts"].sort(
            key=lambda item: (item["role"], item["ref"], item["sha256"])
        )
        for invocation in manifest.get("professional_skill_invocations", []):
            if invocation["schema_version"] == 2:
                invocation_core = {
                    key: deepcopy(value)
                    for key, value in invocation.items()
                    if key != "invocation_ref"
                }
                invocation["invocation_ref"] = cls.professional_invocation_ref(
                    invocation_core
                )
        core = {
            "surface_kind": manifest["surface_kind"],
            "schema_version": manifest["schema_version"],
            "generation_id": manifest["generation_id"],
            "manifest_scope": manifest["manifest_scope"],
            "artifacts": manifest["artifacts"],
        }
        if manifest["schema_version"] == 2:
            from med_autoscience.authority_handlers._generation_manifest import (
                build_review_scopes,
            )

            manifest["review_scopes"] = build_review_scopes(
                manifest["artifacts"], manifest["manifest_scope"]
            )
            core["review_scopes"] = manifest["review_scopes"]
            if "professional_skill_invocations" in manifest:
                core["professional_skill_invocations"] = manifest[
                    "professional_skill_invocations"
                ]
            if "first_draft_quality_application" in manifest:
                core["first_draft_quality_application"] = manifest[
                    "first_draft_quality_application"
                ]
            for field in (
                "clinical_analysis_identity_admission",
                "selected_build_binding",
                "reviewer_response_sync",
            ):
                if field in manifest:
                    core[field] = manifest[field]
        fingerprint = cls.fingerprint(core)
        manifest["generation_manifest_sha256"] = fingerprint
        manifest_ref = {
            "kind": "mas_generation_manifest",
            "ref": (
                f"mas-generation-manifest:{manifest['generation_id']}:"
                f"{manifest['manifest_scope']}:"
                f"{fingerprint.removeprefix('sha256:')}"
            ),
            "size_bytes": len(cls.canonical_bytes(core)),
            "sha256": fingerprint,
        }
        request["generation_manifest_ref"] = manifest_ref
        currentness = request["review_authority"]["currentness_receipt"]
        currentness["current_generation_manifest_ref"] = manifest_ref
        cls.reseal_review_currentness(request)


@pytest.fixture
def authority_records() -> AuthorityRecordFactory:
    return AuthorityRecordFactory()
