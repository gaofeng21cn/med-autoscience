"""Paper mission authority request fixture builder."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from ._candidate import CandidateAdmissionFixtures
from ._review import ReviewFixtures
from .surface_constants import LANES_BY_SCOPE


class PaperMissionFixtures(CandidateAdmissionFixtures, ReviewFixtures):

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
