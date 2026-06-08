from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class OwnerCallable:
    owner: str
    action_type: str
    callable_surface: str
    required_inputs: tuple[str, ...]
    required_outputs: tuple[str, ...]
    artifact_delta_predicate: str
    gate_replay_target: str | None
    idempotency_scope: str
    source_fingerprint_scope: str

    def to_payload(self) -> dict[str, Any]:
        return asdict(self)


_OWNER_CALLABLES: tuple[OwnerCallable, ...] = (
    OwnerCallable(
        owner="MAS/controller",
        action_type="inspect_controller_route",
        callable_surface="paper_progress_reconciler.inspect_controller_route",
        required_inputs=(
            "paper_progress_state",
            "owner_route",
            "authority_snapshot",
        ),
        required_outputs=("MAS controller redrive receipt or typed blocker",),
        artifact_delta_predicate="controller_route_gap_resolved_or_typed_blocker_recorded",
        gate_replay_target=None,
        idempotency_scope="study_quest_owner_route",
        source_fingerprint_scope="owner_route.source_fingerprint",
    ),
    OwnerCallable(
        owner="ai_reviewer",
        action_type="return_to_ai_reviewer_workflow",
        callable_surface="ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow",
        required_inputs=(
            "manuscript",
            "evidence_ledger",
            "review_ledger",
            "study_charter",
            "artifacts/supervision/requests/ai_reviewer/latest.json",
        ),
        required_outputs=("artifacts/publication_eval/latest.json",),
        artifact_delta_predicate="ai_reviewer_judgement_updated",
        gate_replay_target="controller_decisions/latest.json",
        idempotency_scope="study_quest_owner_route",
        source_fingerprint_scope="publication_work_unit_fingerprint",
    ),
    OwnerCallable(
        owner="publication_gate",
        action_type="publication_gate_specificity_required",
        callable_surface="publication_gate.write_gate_files+_materialize_publication_eval_latest",
        required_inputs=("quest_root", "paper_root", "publication_gate_report"),
        required_outputs=("artifacts/publication_eval/latest.json",),
        artifact_delta_predicate="specific_blocker_targets_materialized",
        gate_replay_target="publication_eval/latest.json",
        idempotency_scope="publication_gate_work_unit",
        source_fingerprint_scope="publication_gate.gate_fingerprint",
    ),
    OwnerCallable(
        owner="publication_gate_owner",
        action_type="publication_handoff_owner_gate",
        callable_surface="publication_handoff_owner_gate.evaluate_terminal_handoff",
        required_inputs=(
            "stage_artifact_index.current_stage=08-publication_package_handoff",
            "artifacts/medical_paper/readiness.json",
            "artifacts/stage_outputs/08-publication_package_handoff/publication_package_manifest.json",
            "artifacts/stage_outputs/08-publication_package_handoff/publication_gate_receipt.json",
        ),
        required_outputs=(
            "artifacts/stage_outputs/08-publication_package_handoff/handoff_owner_receipt.json",
            "typed blocker:publication_handoff_owner_gate_blocked",
        ),
        artifact_delta_predicate="handoff_owner_receipt_or_typed_blocker_written",
        gate_replay_target=None,
        idempotency_scope="publication_handoff_owner_gate_work_unit",
        source_fingerprint_scope="stage_artifact_index.next_owner_action.source_ref",
    ),
    OwnerCallable(
        owner="MedAutoScience",
        action_type="complete_medical_paper_readiness_surface",
        callable_surface="medical_paper_readiness.complete_medical_paper_readiness_surface",
        required_inputs=(
            "artifacts/medical_paper/readiness.json",
            "provider-backed capability payload or existing canonical capability surface",
            "artifacts/supervision/requests/medical_paper_readiness/latest.json",
        ),
        required_outputs=(
            "artifacts/medical_paper/readiness.json",
            "typed blocker:medical_paper_readiness_surface_input_required",
        ),
        artifact_delta_predicate="medical_paper_readiness_surface_completed_or_stable_blocker_recorded",
        gate_replay_target="publication_handoff_owner_gate.evaluate_terminal_handoff",
        idempotency_scope="medical_paper_readiness_surface_work_unit",
        source_fingerprint_scope="stage_kernel_projection.current_owner_delta.source_ref",
    ),
    OwnerCallable(
        owner="quality_repair_batch",
        action_type="run_quality_repair_batch",
        callable_surface="quality_repair_batch.run_quality_repair_batch",
        required_inputs=("controller_decisions/latest.json", "publication_eval/latest.json", "paper_root"),
        required_outputs=("paper/*", "artifacts/controller/quality_repair_batch/latest.json"),
        artifact_delta_predicate="canonical_paper_or_quality_repair_artifact_delta",
        gate_replay_target="publication_eval/latest.json",
        idempotency_scope="quality_repair_work_unit",
        source_fingerprint_scope="controller_decision.work_unit_fingerprint",
    ),
    OwnerCallable(
        owner="analysis_harmonization_owner",
        action_type="unit_harmonized_external_validation_rerun",
        callable_surface="analysis_harmonization_owner.unit_harmonized_external_validation_rerun_or_typed_blocker",
        required_inputs=(
            "controller_decisions/latest.json",
            "publication_eval/latest.json",
            "harmonization_route_back/latest.md",
            "analysis inputs",
        ),
        required_outputs=(
            "unit-harmonized external-validation rerun evidence",
            "typed blocker:unit_harmonized_rerun_required",
        ),
        artifact_delta_predicate="unit_harmonized_rerun_evidence_or_analysis_owner_typed_blocker",
        gate_replay_target="publication_eval/latest.json",
        idempotency_scope="analysis_harmonization_work_unit",
        source_fingerprint_scope="controller_decision.work_unit_fingerprint",
    ),
    OwnerCallable(
        owner="source_provenance_owner",
        action_type="recover_transport_model_provenance",
        callable_surface="source_provenance_owner.recover_transport_model_provenance_or_typed_blocker",
        required_inputs=(
            "artifacts/controller/analysis_harmonization/latest.json",
            "artifacts/results/main_result.json",
            "analysis/clean_room_execution/20_transportability/model_spec_and_feature_list.md",
            "legacy runtime result refs",
        ),
        required_outputs=(
            "canonical transport model provenance bundle",
            "typed blocker:transport_model_provenance_recovery_required",
        ),
        artifact_delta_predicate="transport_model_provenance_bundle_or_source_owner_typed_blocker",
        gate_replay_target="analysis_harmonization_owner.unit_harmonized_external_validation_rerun_or_typed_blocker",
        idempotency_scope="source_provenance_recovery_work_unit",
        source_fingerprint_scope="analysis_harmonization_owner_result.blocking_owner_route",
    ),
    OwnerCallable(
        owner="decision",
        action_type="methodology_reframe_route_decision",
        callable_surface="decision_owner.methodology_reframe_route_decision",
        required_inputs=(
            "artifacts/controller/source_provenance/latest.json",
            "artifacts/controller/analysis_harmonization/latest.json",
            "artifacts/controller_decisions/latest.json",
        ),
        required_outputs=("artifacts/controller_decisions/latest.json",),
        artifact_delta_predicate="methodology_reframe_route_decision_written",
        gate_replay_target=None,
        idempotency_scope="methodology_reframe_work_unit",
        source_fingerprint_scope="source_provenance_owner_result.terminal_blocker",
    ),
    OwnerCallable(
        owner="provenance_limited_harmonization_owner",
        action_type="provenance_limited_harmonization_audit",
        callable_surface="provenance_limited_harmonization_owner.provenance_limited_harmonization_audit_or_typed_blocker",
        required_inputs=(
            "artifacts/controller_decisions/latest.json",
            "artifacts/controller/analysis_harmonization/latest.json",
            "artifacts/controller/source_provenance/latest.json",
        ),
        required_outputs=(
            "artifacts/controller/provenance_limited_harmonization/latest.json",
            "typed blocker:provenance_limited_harmonization_audit_required",
        ),
        artifact_delta_predicate="provenance_limited_audit_or_route_typed_blocker",
        gate_replay_target=None,
        idempotency_scope="provenance_limited_harmonization_work_unit",
        source_fingerprint_scope="controller_decision.work_unit_fingerprint",
    ),
    OwnerCallable(
        owner="gate_clearing_batch",
        action_type="run_gate_clearing_batch",
        callable_surface="gate_clearing_batch.run_gate_clearing_batch",
        required_inputs=("publication_eval/latest.json", "publication_gate_report", "paper_root"),
        required_outputs=("artifacts/controller/gate_clearing_batch/latest.json",),
        artifact_delta_predicate="required_repair_units_or_gate_replay_result",
        gate_replay_target="publication_gate.run_controller",
        idempotency_scope="publication_gate_work_unit",
        source_fingerprint_scope="publication_work_unit_fingerprint",
    ),
    OwnerCallable(
        owner="delivery_sync",
        action_type="sync_submission_minimal_delivery",
        callable_surface="study_delivery_sync.sync_study_delivery",
        required_inputs=("paper/submission_minimal", "submission_minimal_manifest", "study_root"),
        required_outputs=("manuscript/current_package", "manuscript/delivery_manifest.json"),
        artifact_delta_predicate="submission_source_or_current_package_freshness_proof",
        gate_replay_target="publication_gate.run_controller",
        idempotency_scope="submission_delivery_source_signature",
        source_fingerprint_scope="submission_minimal.source_signature",
    ),
)


def owner_callable_registry() -> dict[str, dict[str, Any]]:
    return {item.owner: item.to_payload() for item in _OWNER_CALLABLES}


def owner_callable_for_action(action_type: str) -> dict[str, Any] | None:
    normalized = str(action_type or "").strip()
    for item in _OWNER_CALLABLES:
        if item.action_type == normalized:
            return item.to_payload()
    return None


def paper_work_unit_lifecycle_contract() -> dict[str, Any]:
    return {
        "surface_kind": "paper_work_unit_lifecycle_contract",
        "work_units": {
            "run_quality_repair_batch": {
                "owner": "quality_repair_batch",
                "allowed_writes": [
                    "paper/draft.md",
                    "paper/build/review_manuscript.md",
                    "paper/claim_evidence_map.json",
                    "paper/evidence_ledger.json",
                    "artifacts/controller/quality_repair_batch/latest.json",
                    "artifacts/controller/repair_execution_evidence/latest.json",
                    "artifacts/supervision/requests/ai_reviewer/latest.json",
                    "artifacts/controller/gate_replay_requests/latest.json",
                ],
                "forbidden_writes": [
                    "artifacts/publication_eval/latest.json",
                    "controller_decisions/latest.json",
                    "paper/submission_minimal/**",
                    "manuscript/current_package/**",
                ],
                "required_input_refs": [
                    "controller_decisions/latest.json",
                    "publication_eval/latest.json",
                    "paper_root",
                ],
                "required_output_refs": [
                    "paper/*",
                    "artifacts/controller/quality_repair_batch/latest.json",
                ],
                "completion_proof": {
                    "requires_owner_receipt_or_typed_blocker": True,
                    "required_refs": [
                        "owner_receipt_ref",
                        "required_output_ref",
                        "artifact_delta_ref_or_gate_replay_ref_or_typed_blocker_ref",
                    ],
                },
                "next_owner_rules": {
                    "on_completed": [
                        "ai_reviewer",
                        "publication_gate",
                        "delivery_sync",
                        "controller_stop",
                    ],
                    "on_blocked": [
                        "write",
                        "analysis_harmonization_owner",
                        "source_provenance_owner",
                        "decision",
                        "awaiting_human",
                    ],
                },
            },
            "publication_handoff_owner_gate": {
                "owner": "publication_gate_owner",
                "allowed_writes": [
                    "artifacts/stage_outputs/08-publication_package_handoff/handoff_owner_receipt.json",
                    "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json",
                    "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                    "artifacts/stage_outputs/08-publication_package_handoff/stage_manifest.json",
                    "artifacts/stage_outputs/08-publication_package_handoff/current.json",
                    "artifacts/stage_outputs/08-publication_package_handoff/projection/current_owner_delta.json",
                ],
                "forbidden_writes": [
                    "artifacts/publication_eval/latest.json",
                    "controller_decisions/latest.json",
                    "paper/**",
                    "paper/submission_minimal/**",
                    "manuscript/current_package/**",
                ],
                "required_input_refs": [
                    "stage_artifact_index.current_stage=08-publication_package_handoff",
                    "artifacts/medical_paper/readiness.json",
                    "artifacts/stage_outputs/08-publication_package_handoff/publication_package_manifest.json",
                    "artifacts/stage_outputs/08-publication_package_handoff/publication_gate_receipt.json",
                ],
                "required_output_refs": [
                    "artifacts/stage_outputs/08-publication_package_handoff/handoff_owner_receipt.json",
                    "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                ],
                "completion_proof": {
                    "requires_owner_receipt_or_typed_blocker": True,
                    "required_refs": [
                        "owner_receipt_ref_or_typed_blocker_ref",
                        "readiness_ref",
                        "terminal_stage_manifest_ref",
                    ],
                    "publication_ready_claim_authorized": False,
                    "submission_ready_claim_authorized": False,
                    "terminal_projection_writer": (
                        "publication_handoff_stage_projection.py"
                    ),
                },
                "next_owner_rules": {
                    "on_completed": ["human_gate", "controller_stop"],
                    "on_blocked": ["MedAutoScience", "publication_gate_owner", "awaiting_human"],
                },
            },
            "complete_medical_paper_readiness_surface": {
                "owner": "MedAutoScience",
                "allowed_writes": [
                    "artifacts/medical_paper/readiness.json",
                    "artifacts/medical_paper/*.json",
                    "artifacts/medical_paper/actions/**",
                    "artifacts/controller_decisions/latest.json",
                    "artifacts/stage_outputs/08-publication_package_handoff/receipts/owner_receipt.json",
                    "artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json",
                    "artifacts/stage_outputs/08-publication_package_handoff/stage_manifest.json",
                    "artifacts/stage_outputs/08-publication_package_handoff/current.json",
                    "artifacts/stage_outputs/08-publication_package_handoff/projection/current_owner_delta.json",
                ],
                "forbidden_writes": [
                    "artifacts/publication_eval/latest.json",
                    "paper/**",
                    "paper/submission_minimal/**",
                    "manuscript/current_package/**",
                    "artifacts/stage_outputs/08-publication_package_handoff/handoff_owner_receipt.json",
                ],
                "required_input_refs": [
                    "artifacts/medical_paper/readiness.json",
                    "provider-backed capability payload or existing canonical capability surface",
                    "artifacts/supervision/requests/medical_paper_readiness/latest.json",
                ],
                "required_output_refs": [
                    "artifacts/medical_paper/readiness.json",
                    "typed blocker:medical_paper_readiness_surface_input_required",
                ],
                "completion_proof": {
                    "requires_owner_receipt_or_typed_blocker": True,
                    "publication_ready_claim_authorized": False,
                    "submission_ready_claim_authorized": False,
                    "terminal_stage_owner_answer_requires_trusted_opl_binding": True,
                    "terminal_projection_writer": (
                        "publication_handoff_stage_projection.py"
                    ),
                },
                "next_owner_rules": {
                    "on_completed": ["publication_gate_owner", "controller_stop"],
                    "on_blocked": ["MedAutoScience", "awaiting_human"],
                },
            },
            "return_to_ai_reviewer_workflow": {
                "owner": "ai_reviewer",
                "allowed_writes": ["artifacts/publication_eval/latest.json"],
                "forbidden_writes": [
                    "paper/**",
                    "manuscript/current_package/**",
                    "controller_decisions/latest.json",
                ],
                "required_input_refs": [
                    "manuscript",
                    "evidence_ledger",
                    "review_ledger",
                    "study_charter",
                    "artifacts/supervision/requests/ai_reviewer/latest.json",
                ],
                "required_output_refs": ["artifacts/publication_eval/latest.json"],
                "completion_proof": {
                    "requires_owner_receipt_or_typed_blocker": True,
                    "currentness_required": True,
                },
                "next_owner_rules": {
                    "on_completed": ["write", "publication_gate", "delivery_sync", "controller_stop"],
                    "on_blocked": ["ai_reviewer", "write", "awaiting_human"],
                },
            },
        },
    }


def paper_work_unit_lifecycle_for_action(action_type: str) -> dict[str, Any] | None:
    return paper_work_unit_lifecycle_contract()["work_units"].get(str(action_type or "").strip())


def callable_owner_names() -> tuple[str, ...]:
    return tuple(item.owner for item in _OWNER_CALLABLES)


__all__ = [
    "OwnerCallable",
    "callable_owner_names",
    "owner_callable_for_action",
    "owner_callable_registry",
    "paper_work_unit_lifecycle_contract",
    "paper_work_unit_lifecycle_for_action",
]
