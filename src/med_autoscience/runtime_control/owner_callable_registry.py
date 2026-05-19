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
        action_type="runtime_platform_repair",
        callable_surface="domain_route_scan.scan_domain_routes(apply_runtime_platform_repair=True)",
        required_inputs=("owner_route", "runtime_health_snapshot", "controller_decisions/latest.json"),
        required_outputs=("artifacts/supervision/consumer/runtime_platform_repair.json",),
        artifact_delta_predicate="owner_route_advances_or_runtime_repair_receipt",
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


def callable_owner_names() -> tuple[str, ...]:
    return tuple(item.owner for item in _OWNER_CALLABLES)


__all__ = [
    "OwnerCallable",
    "callable_owner_names",
    "owner_callable_for_action",
    "owner_callable_registry",
]
