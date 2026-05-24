from __future__ import annotations

from typing import Any

from med_autoscience.medical_material_passport import SOURCE_ADAPTER_REJECTION_REASONS

SURFACE_KIND = "mas_ars_learning_projection"
SOURCE_REPOSITORY = "https://github.com/Imbad0202/academic-research-skills"
SOURCE_HEAD = "d564d26da39de039ba71d9b51f43e6a25fe9b149"
CONTRACT_REF = "med_autoscience.ars_learning_projection.build_ars_learning_projection"
DOC_REF = "docs/references/mainline/ars_learning_intake.md"


def build_ars_learning_projection() -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "version": "mas-ars-learning-projection.v1",
        "status": "pattern_intake_projected",
        "source_snapshot": {
            "source_project": "academic-research-skills",
            "repository": SOURCE_REPOSITORY,
            "observed_head": SOURCE_HEAD,
            "intake_doc_ref": DOC_REF,
            "dependency_introduced": False,
        },
        "absorbed_patterns": [
            {
                "pattern_id": "claim_citation_support_audit",
                "source_pattern": "claim_ref_alignment_audit_agent",
                "mas_mapping": "claim_evidence_support_projection",
                "source_refs": [
                    "study_charter",
                    "evidence_ledger",
                    "review_ledger",
                    "publication_eval/latest.json",
                ],
                "consumer_role": "stage_quality_input_and_ai_reviewer_context",
                "authority": "projection_only",
            },
            {
                "pattern_id": "data_access_and_oversight_metadata",
                "source_pattern": "ai_disclosure_and_literature_corpus_metadata",
                "mas_mapping": "data_access_oversight_refs",
                "source_refs": [
                    "study_charter",
                    "evidence_ledger",
                    "review_ledger",
                    "progress_projection",
                    "domain_health_diagnostic",
                ],
                "consumer_role": "source_readiness_and_human_gate_context",
                "authority": "projection_only",
            },
            {
                "pattern_id": "evidence_handoff_passport",
                "source_pattern": "passport_as_reset_boundary",
                "mas_mapping": "evidence_handoff_ref_pack",
                "source_refs": [
                    "stage_knowledge_packet",
                    "evidence_ledger",
                    "review_ledger",
                    "controller_decisions/latest.json",
                    "domain_health_diagnostic",
                ],
                "consumer_role": "body_free_handoff_refs_for_opl_stage_runtime",
                "authority": "projection_only",
            },
            {
                "pattern_id": "medical_material_passport_source_handoff",
                "source_pattern": "material_passport_literature_corpus_adapter_and_rejection_log",
                "mas_mapping": "medical_material_passport_refs_and_source_adapter_contract",
                "source_refs": [
                    "source_readiness_refs",
                    "claim_evidence_refs",
                    "review_contract_refs",
                    "artifact_rebuild_refs",
                    "human_decision_refs",
                    "owner_receipt_refs",
                ],
                "consumer_role": "source_workspace_evidence_handoff_refs",
                "authority": "projection_only",
            },
        ],
        "truth_surface_mapping": {
            "claim_support_audit_refs": [
                "study_charter",
                "paper/evidence/evidence_ledger.json",
                "paper/review/review_ledger.json",
                "artifacts/publication_eval/latest.json",
            ],
            "data_access_oversight_refs": [
                "study_charter.data_access",
                "study_charter.oversight",
                "paper/evidence/evidence_ledger.json#source_access",
                "paper/review/review_ledger.json#oversight_review",
                "artifacts/runtime/progress_projection/latest.json",
                "artifacts/runtime/domain_health_diagnostic/latest.json",
            ],
            "handoff_refs": [
                "stage_knowledge_packet",
                "stage_memory_closeout_packet",
                "memory_write_router_receipt",
                "artifacts/controller_decisions/latest.json",
                "artifacts/publication_eval/latest.json",
            ],
            "verdict_refs": [
                "artifacts/publication_eval/latest.json",
                "artifacts/controller_decisions/latest.json",
            ],
            "medical_material_passport_refs": [
                "medical_material_passport.sections.source_readiness_refs",
                "medical_material_passport.sections.claim_evidence_refs",
                "medical_material_passport.sections.review_contract_refs",
                "medical_material_passport.sections.artifact_rebuild_refs",
                "medical_material_passport.sections.human_decision_refs",
                "medical_material_passport.sections.owner_receipt_refs",
            ],
        },
        "source_adapter_contract": {
            "surface_kind": "mas_source_adapter_output",
            "schema_version": "mas-source-adapter-output.v1",
            "contract_ref": "med_autoscience.medical_material_passport.build_source_adapter_output",
            "records_write_mas_truth": False,
            "always_emit_rejection_log": True,
            "closed_reasons": list(SOURCE_ADAPTER_REJECTION_REASONS),
            "entry_level_reject_continues": True,
            "adapter_level_failure_loud": True,
        },
        "metadata_policy": {
            "body_included": False,
            "ars_passport_is_truth": False,
            "ars_passport_body_exported": False,
            "medical_material_passport_body_exported": False,
            "data_access_metadata_authority": "study_charter_and_evidence_ledger",
            "oversight_metadata_authority": "study_charter_review_ledger_and_human_gate",
            "claim_support_authority": "evidence_ledger_review_ledger_and_ai_reviewer_backed_publication_eval",
            "handoff_authority": "mas_stage_packets_controller_decisions_and_owner_receipts",
        },
        "opl_shared_primitive_handoff": {
            "expected_owner": "one-person-lab",
            "primitive_family": [
                "generic_handoff_ledger",
                "generic_passport_resume_boundary",
                "generic_claim_audit_schema",
                "generic_metadata_index",
            ],
            "mas_role": "domain_projection_and_thin_adapter_only",
            "allowed_export": [
                "refs",
                "metadata",
                "freshness",
                "typed_blockers",
                "owner_boundary",
            ],
            "forbidden_export": [
                "memory_body",
                "evidence_ledger_body",
                "review_ledger_body",
                "publication_verdict_body",
                "paper_or_package_blob",
            ],
        },
        "authority_boundary": {
            "domain_truth_owner": "MedAutoScience",
            "medical_quality_owner": "MedAutoScience",
            "publication_verdict_owner": "MedAutoScience",
            "artifact_authority_owner": "MedAutoScience",
            "generic_framework_owner": "one-person-lab",
            "opl_role": "shared_primitive_and_projection_consumer",
            "ars_role": "external_pattern_source_only",
            "can_write_domain_truth": False,
            "can_write_evidence_ledger": False,
            "can_write_review_ledger": False,
            "can_write_publication_eval": False,
            "can_write_controller_decisions": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            "can_authorize_artifact_authority": False,
        },
    }


__all__ = [
    "CONTRACT_REF",
    "DOC_REF",
    "SOURCE_HEAD",
    "SOURCE_REPOSITORY",
    "SOURCE_ADAPTER_REJECTION_REASONS",
    "SURFACE_KIND",
    "build_ars_learning_projection",
]
