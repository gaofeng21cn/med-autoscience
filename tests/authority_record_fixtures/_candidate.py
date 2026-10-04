"""Candidate admission fixture builders."""

from __future__ import annotations

from typing import Any

from ._manifest import GenerationManifestFixtures


class CandidateAdmissionFixtures(GenerationManifestFixtures):

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
