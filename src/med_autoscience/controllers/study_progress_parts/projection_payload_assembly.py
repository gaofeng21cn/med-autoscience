from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import med_autoscience.controllers.pi_action_projection as pi_action_projection
from med_autoscience.paper_mission_opl_readback import (
    paper_mission_next_action_envelope,
)
from med_autoscience.controllers.production_blocker_impact_projection import (
    build_production_blocker_impact_projection,
)
from med_autoscience.controllers.evidence_gap_projection import (
    attach_evidence_gap_projection,
)
from med_autoscience.controllers import study_domain_transition_table
from med_autoscience.controllers.paper_recovery_state import build_paper_recovery_state
from med_autoscience.controllers.study_interventions import read_intervention_events
from med_autoscience.runtime_protocol import evo_scientist_sidecar_refs

from .ai_first_runtime_projection import attach_ai_first_runtime_projection
from .current_owner_handoff_projection import (
    apply_current_owner_handoff_user_visible_status,
)
from .canonical_owner_action_projection import (
    build_canonical_owner_action_projection,
    submission_authority_owner_gate_readback,
)
from .current_owner_action_projection_reconcile import (
    reconcile_current_owner_action_projection,
)
from .macro_state_projection import compact_study_macro_state_from_payload
from .mission_summary import (
    attach_artifact_first_mission_summary,
    refresh_top_level_stage_closure_projection,
    without_legacy_next_action_authority as _without_legacy_next_action_authority,
)
from .opl_supervisor_decision_readback import (
    attach_opl_supervisor_decision_readback as _attach_opl_supervisor_decision_readback,
)
from .progress_first_projection import build_progress_first_projection
from .progress_first_monitoring import build_progress_first_monitoring_summary
from .projection_payload_assembly_helpers import (
    active_run_id_with_live_handoff as _active_run_id_with_live_handoff,
    runtime_refs_with_live_handoff as _runtime_refs_with_live_handoff,
)
from .projection_payload_assembly_refs import build_projection_refs
from .projection_payload_assembly_status import (
    apply_runtime_medical_publication_surface_user_visible_status as _apply_runtime_medical_publication_surface_user_visible_status,
)
from .projection_payload_assembly_parts.ai_first_snapshot_fields import (
    progress_ai_first_and_snapshot_fields as _progress_ai_first_and_snapshot_fields,
)
from .projection_payload_assembly_parts.base_payload_fields import (
    progress_control_contract_fields as _progress_control_contract_fields,
    progress_payload_identity_fields as _progress_payload_identity_fields,
    progress_quality_fields as _progress_quality_fields,
    progress_stage_and_operator_fields as _progress_stage_and_operator_fields,
    progress_supervision_fields as _progress_supervision_fields,
)
from .projection_payload_assembly_parts.progress_delta import (
    progress_delta_metrics as _progress_delta_metrics,
)
from .projection_payload_assembly_parts.paper_recovery_visibility import (
    apply_paper_recovery_state_user_visible_status as _apply_paper_recovery_state_user_visible_status,
)
from .projection_payload_assembly_parts.paper_recovery_execution_refresh import (
    normalize_paper_recovery_execution_projection as _normalize_paper_recovery_execution_projection,
)
from .projection_payload_assembly_parts.payload_sync import (
    sync_progress_first_owner_action_admission as _sync_progress_first_owner_action_admission,
    sync_study_macro_state_from_user_visible_projection as _sync_study_macro_state_from_user_visible_projection,
)
from .projection_payload_assembly_parts.publication_runtime_fields import (
    progress_publication_and_runtime_fields as _progress_publication_and_runtime_fields,
)
from .projection_payload_assembly_parts.current_execution_surfaces import (
    refresh_current_execution_surfaces as _refresh_current_execution_surfaces,
)
from .projection_payload_assembly_parts.current_work_unit_typed_blocker_status import (
    apply_current_work_unit_typed_blocker_user_visible_status as _apply_current_work_unit_typed_blocker_user_visible_status,
)
from .projection_payload_assembly_parts.running_provider_status import (
    apply_running_provider_attempt_top_level_status,
)
from .projection_payload_assembly_parts.supervision_sync import (
    sync_supervision_from_user_visible_projection as _sync_supervision_from_user_visible_projection,
)
from .projection_payload_assembly_parts.terminal_consumption_identity import (
    provider_admission_candidate_payload as _provider_admission_candidate_payload,
    terminal_consumption_candidates_from_payload as _terminal_consumption_candidates_from_payload,
    terminal_consumption_matches_current_pending_identity as _terminal_consumption_matches_current_pending_identity,
    transition_request_candidates_from_payload as _transition_request_candidates_from_payload,
)
from .projection_payload_assembly_parts.terminal_delivery_status import (
    apply_terminal_delivery_user_visible_status as _apply_terminal_delivery_user_visible_status,
)
from .projection_payload_assembly_parts.typed_blocker_resolution_successor import (
    attach_typed_blocker_resolution_successor_projection as _attach_typed_blocker_resolution_successor_projection,
)
from .provider_admission_projection import provider_admission_projection_fields
from .opl_current_control_state_handoff import refresh_handoff_with_terminal_closeout_candidates
from .repair_progress_projection import build_repair_progress_projection
from .research_pack_progress_projection import build_research_pack_progress_summary_projection
from .shared import _mapping_copy, _non_empty_text
from .stage_kernel_projection import stage_kernel_projection_from_artifact_index
from .user_visible_projection import build_user_visible_projection


def assemble_study_progress_payload(
    *,
    generated_at: str,
    study_id: str,
    study_root: Path,
    quest_id: str | None,
    quest_root: Path | None,
    current_stage: str,
    current_stage_summary: str,
    paper_stage: str | None,
    paper_stage_summary: str,
    status_narration_contract: dict[str, Any],
    latest_events: list[dict[str, Any]],
    current_blockers: list[str],
    next_system_action: str,
    current_active_run_id: str | None,
    auto_runtime_parked: dict[str, Any],
    intervention_lane: dict[str, Any],
    operator_verdict: dict[str, Any],
    operator_status_card: dict[str, Any],
    recommended_command: str | None,
    recommended_commands: list[dict[str, Any]],
    autonomy_contract: dict[str, Any],
    autonomy_soak_status: dict[str, Any],
    recovery_contract: dict[str, Any],
    needs_physician_decision: bool,
    physician_decision_summary: str | None,
    status: dict[str, Any],
    continuation_state: dict[str, Any],
    family_checkpoint_lineage: dict[str, Any],
    interaction_arbitration: dict[str, Any],
    manual_finish_contract: dict[str, Any] | None,
    task_intake: dict[str, Any],
    progress_freshness: dict[str, Any],
    quality_closure_truth: dict[str, Any],
    quality_execution_lane: dict[str, Any],
    same_line_route_truth: dict[str, Any],
    same_line_route_surface: dict[str, Any],
    quality_closure_basis: dict[str, Any],
    quality_review_agenda: dict[str, Any],
    quality_revision_plan: dict[str, Any],
    quality_review_loop: dict[str, Any],
    quality_repair_batch_followthrough: dict[str, Any],
    gate_clearing_batch_followthrough: dict[str, Any],
    quality_review_followthrough: dict[str, Any],
    medical_writing_quality_surfaces: dict[str, Any],
    medical_paper_readiness_surface: dict[str, Any],
    medical_paper_ops_health_surface: dict[str, Any],
    artifact_runtime_proof_surface: dict[str, Any],
    submission_hygiene_truth: dict[str, Any],
    delivery_inspection: dict[str, Any] | None,
    research_runtime_control_projection: dict[str, Any],
    open_auto_research_state: dict[str, Any],
    ai_reviewer_request_lifecycle: dict[str, Any] | None,
    opl_current_control_state_handoff: dict[str, Any] | None,
    runtime_medical_publication_surface: dict[str, Any] | None,
    gate_specificity_request: dict[str, Any] | None,
    ai_first_default_entry_state: dict[str, Any],
    paper_orchestra_operator_projection: dict[str, Any],
    ai_first_observability_snapshots: dict[str, Any],
    ai_first_operations_dashboard: dict[str, Any],
    study_truth_snapshot: dict[str, Any],
    runtime_health_snapshot: dict[str, Any],
    authority_snapshot: dict[str, Any],
    module_surfaces: dict[str, Any],
    runtime_efficiency: dict[str, Any],
    paper_progress_stall: dict[str, Any],
    outer_supervision_slo: dict[str, Any],
    autonomy_slo_status: dict[str, Any] | None,
    ai_doctor_state: dict[str, Any],
    repair_recommendation: dict[str, Any],
    ai_repair_lifecycle: dict[str, Any] | None,
    publication_eval_payload: dict[str, Any] | None,
    stage_artifact_index: dict[str, Any] | None,
    autonomous_runtime_notice: dict[str, Any],
    execution_owner_guard: dict[str, Any],
    supervisor_tick_audit: dict[str, Any],
    runtime_facts: Any,
    supervision_health_status: str | None,
    refs: dict[str, Any],
    profile: Any | None = None,
    materialize_sidecar_observation: bool = False,
    enable_opl_live_provider_attempt_probe: bool = True,
) -> dict[str, Any]:
    handoff = _mapping_copy(opl_current_control_state_handoff)
    repair_progress_projection = build_repair_progress_projection(study_root=study_root)
    current_active_run_id = _active_run_id_with_live_handoff(
        current_active_run_id,
        handoff=handoff,
    )
    progress_delta = _progress_delta_metrics(
        quality_repair_batch_followthrough=quality_repair_batch_followthrough,
        gate_clearing_batch_followthrough=gate_clearing_batch_followthrough,
        opl_current_control_state_handoff=opl_current_control_state_handoff,
        repair_progress_projection=repair_progress_projection,
        runtime_efficiency=runtime_efficiency,
    )
    research_pack_progress_summary = build_research_pack_progress_summary_projection(
        opl_current_control_state_handoff=opl_current_control_state_handoff,
    )
    payload = {
        **_progress_payload_identity_fields(
            generated_at=generated_at,
            study_id=study_id,
            study_root=study_root,
            quest_id=quest_id,
            quest_root=quest_root,
            study_truth_snapshot=study_truth_snapshot,
            runtime_health_snapshot=runtime_health_snapshot,
        ),
        **_progress_stage_and_operator_fields(
            current_stage=current_stage,
            current_stage_summary=current_stage_summary,
            paper_stage=paper_stage,
            paper_stage_summary=paper_stage_summary,
            status_narration_contract=status_narration_contract,
            latest_events=latest_events,
            current_blockers=current_blockers,
            next_system_action=next_system_action,
            current_active_run_id=current_active_run_id,
            auto_runtime_parked=auto_runtime_parked,
            intervention_lane=intervention_lane,
            operator_verdict=operator_verdict,
            operator_status_card=operator_status_card,
            recommended_command=recommended_command,
            recommended_commands=recommended_commands,
        ),
        **_progress_control_contract_fields(
            autonomy_contract=autonomy_contract,
            autonomy_soak_status=autonomy_soak_status,
            recovery_contract=recovery_contract,
            needs_physician_decision=needs_physician_decision,
            physician_decision_summary=physician_decision_summary,
            status=status,
            continuation_state=continuation_state,
            family_checkpoint_lineage=family_checkpoint_lineage,
            interaction_arbitration=interaction_arbitration,
            manual_finish_contract=manual_finish_contract,
            task_intake=task_intake,
            progress_freshness=progress_freshness,
        ),
        **_progress_quality_fields(
            quality_closure_truth=quality_closure_truth,
            quality_execution_lane=quality_execution_lane,
            same_line_route_truth=same_line_route_truth,
            same_line_route_surface=same_line_route_surface,
            quality_closure_basis=quality_closure_basis,
            quality_review_agenda=quality_review_agenda,
            quality_revision_plan=quality_revision_plan,
            quality_review_loop=quality_review_loop,
            quality_repair_batch_followthrough=quality_repair_batch_followthrough,
            gate_clearing_batch_followthrough=gate_clearing_batch_followthrough,
            quality_review_followthrough=quality_review_followthrough,
        ),
        "repair_progress_projection": repair_progress_projection,
        **_progress_publication_and_runtime_fields(
            medical_writing_quality_surfaces=medical_writing_quality_surfaces,
            medical_paper_readiness_surface=medical_paper_readiness_surface,
            medical_paper_ops_health_surface=medical_paper_ops_health_surface,
            artifact_runtime_proof_surface=artifact_runtime_proof_surface,
            submission_hygiene_truth=submission_hygiene_truth,
            delivery_inspection=delivery_inspection,
            research_runtime_control_projection=research_runtime_control_projection,
            open_auto_research_state=open_auto_research_state,
            ai_reviewer_request_lifecycle=ai_reviewer_request_lifecycle,
            opl_current_control_state_handoff=opl_current_control_state_handoff,
            runtime_medical_publication_surface=runtime_medical_publication_surface,
            gate_specificity_request=gate_specificity_request,
        ),
        **_progress_ai_first_and_snapshot_fields(
            ai_first_default_entry_state=ai_first_default_entry_state,
            paper_orchestra_operator_projection=paper_orchestra_operator_projection,
            ai_first_observability_snapshots=ai_first_observability_snapshots,
            ai_first_operations_dashboard=ai_first_operations_dashboard,
            study_truth_snapshot=study_truth_snapshot,
            runtime_health_snapshot=runtime_health_snapshot,
            authority_snapshot=authority_snapshot,
            module_surfaces=module_surfaces,
            runtime_efficiency=runtime_efficiency,
            paper_progress_stall=paper_progress_stall,
            outer_supervision_slo=outer_supervision_slo,
            autonomy_slo_status=autonomy_slo_status,
            ai_doctor_state=ai_doctor_state,
            repair_recommendation=repair_recommendation,
            ai_repair_lifecycle=ai_repair_lifecycle,
        ),
        "supervision": _progress_supervision_fields(
            autonomous_runtime_notice=autonomous_runtime_notice,
            current_active_run_id=current_active_run_id,
            supervision_health_status=supervision_health_status,
            supervisor_tick_audit=supervisor_tick_audit,
            refs=refs,
        ),
        "opl_runtime_refs": _runtime_refs_with_live_handoff(
            runtime_facts.to_runtime_refs_dict(),
            handoff=handoff,
        ),
        "deliverable_progress_delta": progress_delta["deliverable_progress_delta"],
        "paper_progress_delta": progress_delta["paper_progress_delta"],
        "platform_repair_delta": progress_delta["platform_repair_delta"],
        "progress_delta_classification": progress_delta["progress_delta_classification"],
        "research_pack_progress_summary": research_pack_progress_summary,
        "publication_eval": publication_eval_payload,
        "study_intervention_events": read_intervention_events(study_root=study_root),
        "refs": refs,
    }
    payload = _attach_opl_supervisor_decision_readback(payload, profile=profile)
    if stage_artifact_index is not None:
        payload["stage_artifact_index"] = dict(stage_artifact_index)
        payload["stage_kernel_projection"] = stage_kernel_projection_from_artifact_index(
            stage_artifact_index
        )
    payload.update(build_progress_first_projection(payload))
    payload = _attach_fresh_domain_transition(
        payload=payload,
        study_root=study_root,
        status=status,
        current_active_run_id=current_active_run_id,
        publication_eval_payload=publication_eval_payload,
    )
    payload["production_blocker_impact"] = build_production_blocker_impact_projection(
        payload,
        status,
        study_id=study_id,
    )
    payload["current_executable_owner_action"] = None
    payload = reconcile_current_owner_action_projection(payload)
    payload["pi_action_projection"] = pi_action_projection.build_pi_action_projection(payload)
    payload["user_visible_projection"] = build_user_visible_projection(payload)
    payload = _attach_single_next_action_projection(payload)
    handoff = _mapping_copy(payload.get("opl_current_control_state_handoff"))
    payload = _refresh_current_execution_surfaces(
        payload=payload,
        status=status,
        handoff=handoff,
        runtime_health_snapshot=runtime_health_snapshot,
    )
    payload = apply_current_owner_handoff_user_visible_status(payload)
    payload = _apply_runtime_medical_publication_surface_user_visible_status(payload)
    payload = _apply_terminal_delivery_user_visible_status(payload)
    payload["progress_first_monitoring_summary"] = build_progress_first_monitoring_summary(
        {**payload, "execution_owner_guard": execution_owner_guard}
    )
    payload = _apply_provider_admission_fields_with_terminal_probe(
        payload=payload,
        handoff=handoff,
        study_root=study_root,
        profile=profile,
        study_id=study_id,
    )
    handoff = _mapping_copy(payload.get("opl_current_control_state_handoff"))
    payload = _sync_progress_first_owner_action_admission(payload)
    payload["paper_recovery_state"] = build_paper_recovery_state(payload)
    payload = _normalize_paper_recovery_execution_projection(
        payload=payload,
        status=status,
        handoff=handoff,
        runtime_health_snapshot=runtime_health_snapshot,
        study_root=study_root,
        build_canonical_owner_action_projection=build_canonical_owner_action_projection,
        refresh_current_execution_surfaces=_refresh_current_execution_surfaces,
        provider_admission_projection_fields=provider_admission_projection_fields,
        sync_progress_first_owner_action_admission=_sync_progress_first_owner_action_admission,
        build_paper_recovery_state=build_paper_recovery_state,
    )
    payload = attach_evidence_gap_projection(payload)
    payload = _apply_paper_recovery_state_user_visible_status(payload)
    payload["user_visible_projection"] = build_user_visible_projection(payload)
    payload = _apply_post_user_visible_status_overrides(payload)
    payload = _sync_study_macro_state_from_user_visible_projection(payload)
    if materialize_sidecar_observation:
        payload["evo_scientist_sidecar_observation"] = (
            evo_scientist_sidecar_refs.observe_current_owner_payload(
                study_root=study_root,
                progress_payload=payload,
                apply=True,
            )
        )
    else:
        payload["evo_scientist_sidecar_observation"] = (
            evo_scientist_sidecar_refs.read_latest_evo_scientist_sidecar_projection(
                study_root=study_root,
            )
        )
    payload = _apply_provider_admission_fields_with_terminal_probe(
        payload=payload,
        handoff=_mapping_copy(payload.get("opl_current_control_state_handoff")),
        study_root=study_root,
        profile=profile,
        study_id=study_id,
    )
    payload = attach_ai_first_runtime_projection(
        payload,
        study_root=study_root,
        generated_at=generated_at,
    )
    payload = _sync_supervision_from_user_visible_projection(payload)
    payload = attach_artifact_first_mission_summary(
        payload,
        enable_opl_live_probe=enable_opl_live_provider_attempt_probe,
    )
    payload = _attach_single_next_action_projection(payload)
    payload = _attach_typed_blocker_resolution_successor_projection(
        payload=payload,
        profile=profile,
        study_id=study_id,
    )
    payload = _attach_submission_authority_owner_gate_readback(payload)
    payload = refresh_top_level_stage_closure_projection(payload)
    payload = apply_running_provider_attempt_top_level_status(payload)
    return _without_legacy_next_action_authority(payload)


def _attach_submission_authority_owner_gate_readback(payload: Mapping[str, Any]) -> dict[str, Any]:
    readback = submission_authority_owner_gate_readback(
        payload,
        next_action=_mapping_copy(payload.get("next_action")),
    )
    if readback is None:
        return dict(payload)
    updated = dict(payload)
    updated["submission_authority_owner_gate_readback"] = readback
    updated["current_executable_owner_action"] = None
    updated.pop("next_action", None)
    updated.pop("canonical_next_action_source", None)
    transaction_readback = _mapping_copy(updated.get("paper_mission_transaction_readback"))
    if transaction_readback:
        transaction_readback.pop("next_action", None)
        updated["paper_mission_transaction_readback"] = transaction_readback
    return updated


def _attach_single_next_action_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    updated = dict(payload)
    existing = _mapping_copy(updated.get("next_action"))
    if existing:
        updated["next_action"] = existing
        updated["canonical_next_action_source"] = (
            _non_empty_text(updated.get("canonical_next_action_source"))
            or "precomputed_canonical_next_action"
        )
        return _sync_user_visible_next_action_owner(updated)
    handoff = _mapping_copy(updated.get("opl_current_control_state_handoff"))
    transaction = _mapping_copy(updated.get("paper_mission_transaction"))
    summary = _mapping_copy(updated.get("artifact_first_mission_summary"))
    if not transaction:
        transaction = _mapping_copy(
            _mapping_copy(summary.get("paper_mission_run")).get(
                "paper_mission_transaction"
            )
        )
    if _has_legacy_progress_fallback_summary(summary):
        return _sync_user_visible_next_action_owner(updated)
    envelope = paper_mission_next_action_envelope(
        transaction=transaction,
        stage_terminal_decision=_mapping_copy(updated.get("stage_terminal_decision")),
        opl_route_command=_mapping_copy(updated.get("opl_route_command")),
        opl_runtime_carrier=_mapping_copy(updated.get("opl_runtime_carrier")),
        opl_route_handoff=handoff,
        diagnostic_refs=[
            ref
            for ref in (
                _non_empty_text(
                    _mapping_copy(updated.get("stage_closure_decision")).get(
                        "decision_ref"
                    )
                ),
            )
            if ref is not None
        ],
    )
    if envelope is not None:
        updated["next_action"] = envelope
        updated["canonical_next_action_source"] = "paper_mission_next_action_envelope"
    return _sync_user_visible_next_action_owner(updated)


def _has_legacy_progress_fallback_summary(summary: Mapping[str, Any]) -> bool:
    read_model_source = _mapping_copy(summary.get("read_model_source"))
    return (
        _non_empty_text(read_model_source.get("source_kind"))
        == "legacy_progress_projection_fallback"
    )


def _sync_user_visible_next_action_owner(payload: Mapping[str, Any]) -> dict[str, Any]:
    user_visible = _mapping_copy(payload.get("user_visible_projection"))
    next_action = _mapping_copy(payload.get("next_action"))
    owner = _non_empty_text(next_action.get("next_owner")) or _non_empty_text(next_action.get("owner"))
    if not user_visible or owner is None:
        return dict(payload)
    updated = dict(payload)
    user_visible["next_owner"] = owner
    user_visible["conditions"] = [
        _synced_next_owner_condition(condition, owner=owner)
        for condition in user_visible.get("conditions") or []
        if isinstance(condition, Mapping)
    ]
    updated["user_visible_projection"] = user_visible
    return updated


def _synced_next_owner_condition(condition: Mapping[str, Any], *, owner: str) -> dict[str, Any]:
    if _non_empty_text(condition.get("type")) != "next_owner":
        return dict(condition)
    return {
        **dict(condition),
        "status": "true",
        "reason": "next_owner_present",
        "message": owner,
    }


def _apply_post_user_visible_status_overrides(payload: dict[str, Any]) -> dict[str, Any]:
    updated = apply_running_provider_attempt_top_level_status(payload)
    updated = apply_current_owner_handoff_user_visible_status(updated)
    updated = _apply_paper_recovery_state_user_visible_status(updated)
    updated = _apply_current_work_unit_typed_blocker_user_visible_status(updated)
    updated = _apply_runtime_medical_publication_surface_user_visible_status(updated)
    updated = _sync_supervision_from_user_visible_projection(updated)
    return _apply_terminal_delivery_user_visible_status(updated)


def _apply_provider_admission_fields_with_terminal_probe(
    *,
    payload: dict[str, Any],
    handoff: Mapping[str, Any],
    study_root: Path,
    profile: Any | None,
    study_id: str,
) -> dict[str, Any]:
    updated = dict(payload)
    if profile is not None:
        original_handoff = _mapping_copy(handoff)
        terminal_consumption_candidates = _terminal_consumption_candidates_from_payload(updated)
        refreshed_handoff = refresh_handoff_with_terminal_closeout_candidates(
            profile=profile,
            study_id=study_id,
            handoff=handoff,
            candidates=terminal_consumption_candidates,
        )
        if refreshed_handoff and refreshed_handoff != dict(handoff):
            updated["opl_current_control_state_handoff"] = refreshed_handoff
            updated.pop("provider_admission_terminal_closeout_consumed", None)
            handoff = refreshed_handoff
            consumed = _mapping_copy(refreshed_handoff.get("provider_admission_terminal_closeout_consumed"))
            if consumed:
                if not _terminal_consumption_matches_current_pending_identity(
                    consumed=consumed,
                    payload={
                        **updated,
                        "provider_admission_candidates": terminal_consumption_candidates,
                    },
                ):
                    updated["opl_current_control_state_handoff"] = original_handoff
                    updated.pop("provider_admission_terminal_closeout_consumed", None)
                    handoff = original_handoff
                else:
                    return _payload_with_terminal_consumed_current_action_suppression({
                        **updated,
                        "provider_admission_pending_count": 0,
                        "provider_admission_candidates": [],
                        "transition_request_pending_count": 0,
                        "transition_request_candidates": [],
                        "provider_admission_terminal_closeout_consumed": consumed,
                    })
    provider_fields = provider_admission_projection_fields(
        payload=_provider_admission_candidate_payload(updated),
        handoff=handoff,
        study_root=study_root,
    )
    updated.update(provider_fields)
    if (
        profile is None
        or (
            int(updated.get("transition_request_pending_count") or 0) <= 0
            and int(updated.get("provider_admission_pending_count") or 0) <= 0
        )
    ):
        return _payload_with_terminal_consumed_current_action_suppression(updated)
    candidates = _terminal_consumption_candidates_from_payload(updated)
    refreshed_handoff = refresh_handoff_with_terminal_closeout_candidates(
        profile=profile,
        study_id=study_id,
        handoff=handoff,
        candidates=candidates,
    )
    if not refreshed_handoff or refreshed_handoff == dict(handoff):
        return updated
    updated["opl_current_control_state_handoff"] = refreshed_handoff
    updated.pop("provider_admission_terminal_closeout_consumed", None)
    consumed = _mapping_copy(refreshed_handoff.get("provider_admission_terminal_closeout_consumed"))
    if consumed:
        if not _terminal_consumption_matches_current_pending_identity(
            consumed=consumed,
            payload=updated,
        ):
            updated["opl_current_control_state_handoff"] = dict(handoff)
            updated.pop("provider_admission_terminal_closeout_consumed", None)
            return updated
        return _payload_with_terminal_consumed_current_action_suppression({
            **updated,
            "provider_admission_pending_count": 0,
            "provider_admission_candidates": [],
            "transition_request_pending_count": 0,
            "transition_request_candidates": [],
            "provider_admission_terminal_closeout_consumed": consumed,
        })
    handoff = refreshed_handoff
    updated.update(
        provider_admission_projection_fields(
            payload=updated,
            handoff=handoff,
            study_root=study_root,
        )
    )
    updated["progress_first_monitoring_summary"] = build_progress_first_monitoring_summary(
        updated
    )
    return _payload_with_terminal_consumed_current_action_suppression(updated)


def _payload_with_terminal_consumed_current_action_suppression(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    updated = dict(payload)
    consumed = _mapping_copy(updated.get("provider_admission_terminal_closeout_consumed"))
    if not consumed:
        return updated
    current_action = _mapping_copy(updated.get("current_executable_owner_action"))
    if current_action and _terminal_consumption_matches_current_pending_identity(
        consumed=consumed,
        payload={"current_executable_owner_action": current_action},
    ):
        updated["current_executable_owner_action"] = None
    current_work_unit = _mapping_copy(updated.get("current_work_unit"))
    if current_work_unit and _terminal_consumption_matches_current_pending_identity(
        consumed=consumed,
        payload={"current_work_unit": current_work_unit},
    ):
        state = dict(_mapping_copy(current_work_unit.get("state")))
        state.update(
            {
                "provider_admission_pending": False,
                "transition_request_pending": False,
                "provider_attempt_or_lease_required": False,
                "provider_admission_requires_opl_runtime_result": False,
                "provider_admission_terminal_consumed": True,
                "provider_admission_terminal_consumed_readback": dict(consumed),
            }
        )
        current_work_unit["state"] = {
            key: value for key, value in state.items() if value not in (None, "", [], {})
        }
        updated["current_work_unit"] = current_work_unit
    return updated


def _attach_fresh_domain_transition(
    *,
    payload: dict[str, Any],
    study_root: Path,
    status: Mapping[str, Any],
    current_active_run_id: str | None,
    publication_eval_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    updated = dict(payload)
    macro_state = compact_study_macro_state_from_payload(updated) or {}
    delivered_package = _mapping_copy(updated.get("delivered_package"))
    transition = study_domain_transition_table.project_domain_transition(
        study_id=_non_empty_text(updated.get("study_id")) or "unknown-study",
        study_root=study_root,
        status={
            **status,
            **updated,
            **({"publication_eval": publication_eval_payload} if publication_eval_payload else {}),
        },
        macro_state=macro_state,
        active_run_id=current_active_run_id,
        running_provider_attempt=_running_provider_attempt_from_payload(updated),
        delivered_package=delivered_package if delivered_package else None,
    )
    if transition and _fresh_domain_transition_should_attach(transition):
        updated["domain_transition"] = transition
    return updated


def _fresh_domain_transition_should_attach(transition: Mapping[str, Any]) -> bool:
    decision_type = _non_empty_text(transition.get("decision_type"))
    if decision_type is None:
        return False
    if decision_type == "fail_closed":
        return False
    return True


def _running_provider_attempt_from_payload(payload: Mapping[str, Any]) -> bool | None:
    handoff = _mapping_copy(payload.get("opl_current_control_state_handoff"))
    if handoff.get("running_provider_attempt") is True:
        return True
    if handoff.get("running_provider_attempt") is False:
        return False
    envelope = _mapping_copy(payload.get("current_execution_envelope"))
    if _non_empty_text(envelope.get("state_kind")) == "running_provider_attempt":
        return True
    return None
