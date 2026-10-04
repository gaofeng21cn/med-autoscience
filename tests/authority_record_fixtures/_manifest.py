"""Generation manifest fixture builder."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from ._professional_quality import ProfessionalQualityFixtures
from .surface_constants import (
    ANALYSIS_ROLES,
    FIRST_DRAFT_ROLE_BY_REF_FIELD,
    ROLES_BY_SCOPE,
    SELECTED_BUILD_ROLE_BY_REF_FIELD,
)


class GenerationManifestFixtures(ProfessionalQualityFixtures):

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
