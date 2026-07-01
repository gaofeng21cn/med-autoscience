from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import med_autoscience.controllers.pi_action_projection as pi_action_projection
from med_autoscience.paper_mission_opl_readback import (
    paper_mission_next_action_envelope,
)
from med_autoscience.controllers.next_action_envelope import (
    compile_next_action_envelope,
)
from med_autoscience.controllers.paper_mission_typed_blocker_resolution import (
    latest_typed_blocker_resolution_readback,
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
    owner_action_next_step,
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
    typed_blocker_reason as _typed_blocker_reason,
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


def _attach_typed_blocker_resolution_successor_projection(
    *,
    payload: Mapping[str, Any],
    profile: Any | None,
    study_id: str,
) -> dict[str, Any]:
    workspace_root = getattr(profile, "workspace_root", None)
    if workspace_root is None:
        return dict(payload)
    readback = latest_typed_blocker_resolution_readback(
        workspace_root=Path(workspace_root),
        study_id=study_id,
    )
    envelope = _typed_blocker_resolution_successor_envelope(
        payload=payload,
        readback=readback,
        study_id=study_id,
    )
    if envelope is None:
        return dict(payload)
    updated = dict(payload)
    updated["typed_blocker_resolution_readback"] = readback
    updated["next_action"] = envelope
    updated["canonical_next_action_source"] = "paper_mission_typed_blocker_resolution"
    updated["current_executable_owner_action"] = build_canonical_owner_action_projection(updated)
    return _promote_typed_blocker_resolution_owner_action(updated)


def _promote_typed_blocker_resolution_owner_action(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    current_action = _mapping_copy(payload.get("current_executable_owner_action"))
    if not current_action:
        return dict(payload)
    owner = _non_empty_text(current_action.get("next_owner")) or "mas_authority_kernel"
    action_type = _non_empty_text(current_action.get("action_type"))
    work_unit_id = _non_empty_text(current_action.get("work_unit_id"))
    next_step = owner_action_next_step(current_action) or (
        f"等待 {owner} owner 处理当前 typed-blocker resolution owner action。"
    )
    blocker = _typed_blocker_resolution_blocker(payload)
    current_blockers = _typed_blocker_resolution_current_blockers(
        payload.get("current_blockers"),
        blocker=blocker,
    )
    summary = _typed_blocker_resolution_summary(
        owner=owner,
        action_type=action_type,
        work_unit_id=work_unit_id,
        blocker=blocker,
    )
    updated = dict(payload)
    updated["current_stage"] = "owner_action_ready"
    updated["current_stage_summary"] = summary
    updated["paper_stage"] = (
        _non_empty_text(updated.get("paper_stage")) or "publishability_gate_blocked"
    )
    updated["paper_stage_summary"] = summary
    updated["runtime_decision"] = "owner_action_required"
    updated["runtime_reason"] = "typed_blocker_resolution_owner_action_ready"
    updated["current_blockers"] = current_blockers
    updated["next_system_action"] = next_step
    updated["needs_user_decision"] = True
    updated["needs_physician_decision"] = True
    updated["physician_decision_summary"] = summary
    updated["user_decision_summary"] = summary
    updated["paper_facing_action"] = _owner_action_paper_facing_action(current_action)
    updated["study_macro_state"] = _typed_blocker_resolution_macro_state(
        payload.get("study_macro_state"),
        owner=owner,
        action_type=action_type,
        work_unit_id=work_unit_id,
        blocker=blocker,
    )
    updated["user_visible_projection"] = _typed_blocker_resolution_user_visible(
        updated.get("user_visible_projection"),
        current_action=current_action,
        current_blockers=current_blockers,
        next_step=next_step,
        summary=summary,
        owner=owner,
    )
    updated["status_narration_contract"] = (
        _typed_blocker_resolution_status_narration_contract(
            updated.get("status_narration_contract"),
            current_blockers=current_blockers,
            next_step=next_step,
            summary=summary,
        )
    )
    return updated


def _typed_blocker_resolution_blocker(payload: Mapping[str, Any]) -> str:
    readback = _mapping_copy(payload.get("typed_blocker_resolution_readback"))
    typed_blocker = _mapping_copy(readback.get("typed_blocker"))
    successor = _mapping_copy(readback.get("successor_work_unit"))
    action = _mapping_copy(payload.get("current_executable_owner_action"))
    paper_delta = _mapping_copy(action.get("paper_facing_delta"))
    return (
        _non_empty_text(typed_blocker.get("blocker_type"))
        or _non_empty_text(successor.get("successor_reason"))
        or _non_empty_text(paper_delta.get("expected_delta"))
        or "paper_mission_stage_route_domain_gate_pending"
    )


def _typed_blocker_resolution_current_blockers(
    value: object,
    *,
    blocker: str,
) -> list[str]:
    stale_fragments = (
        "quest user paused requires explicit wakeup",
        "explicit wakeup",
        "OPL current_control_state handoff",
        "provider admission",
        "runtime owner",
    )
    blockers = [blocker]
    for item in value or []:
        text = _non_empty_text(item)
        if text is None:
            continue
        if any(fragment in text for fragment in stale_fragments):
            continue
        if text not in blockers:
            blockers.append(text)
    return blockers[:8]


def _typed_blocker_resolution_summary(
    *,
    owner: str,
    action_type: str | None,
    work_unit_id: str | None,
    blocker: str,
) -> str:
    action = action_type or "typed-blocker resolution owner action"
    work_unit = f"，work unit={work_unit_id}" if work_unit_id else ""
    return (
        f"OPL terminal receipt 已被 MAS 消费为 typed blocker；当前需 {owner} "
        f"处理 {action}{work_unit}。当前阻塞：{blocker}。"
    )


def _typed_blocker_resolution_macro_state(
    value: object,
    *,
    owner: str,
    action_type: str | None,
    work_unit_id: str | None,
    blocker: str,
) -> dict[str, Any]:
    macro = _mapping_copy(value)
    details = _mapping_copy(macro.get("details"))
    details.update(
        {
            "paper_stage": "publishability_gate_blocked",
            "reason_separation": {
                "control_reason_policy": "typed_blocker_resolution_owner_action",
                "diagnostic_reason_policy": "legacy_runtime_pause_demoted",
            },
            "next_work_unit": work_unit_id,
            "route_owner": owner,
            "action_type": action_type,
            "typed_blocker": blocker,
        }
    )
    macro.update(
        {
            "surface": "study_macro_state",
            "schema_version": 1,
            "writer_state": "owner_action_ready",
            "user_next": "decide",
            "reason": "typed_blocker_resolution_owner_action_ready",
            "details": {key: item for key, item in details.items() if item not in (None, "", [], {})},
            "suppression_reason": "typed_blocker_resolution_successor_promoted",
        }
    )
    return macro


def _typed_blocker_resolution_user_visible(
    value: object,
    *,
    current_action: Mapping[str, Any],
    current_blockers: list[str],
    next_step: str,
    summary: str,
    owner: str,
) -> dict[str, Any]:
    user_visible = _mapping_copy(value)
    user_visible.update(
        {
            "state": "owner_action_ready/decide/typed_blocker_resolution",
            "writer_state": "owner_action_ready",
            "user_next": "decide",
            "reason": "typed_blocker_resolution_owner_action_ready",
            "package_delivered": False,
            "actual_write_active": False,
            "meaningful_artifact_delta": False,
            "next_owner": owner,
            "why_not_progressing": current_blockers[0] if current_blockers else None,
            "user_action_required": True,
            "state_label": "MAS owner action ready",
            "state_summary": summary,
            "current_stage": "owner_action_ready",
            "current_stage_label": "MAS owner action ready",
            "current_stage_summary": summary,
            "status_summary": summary,
            "paper_stage": "publishability_gate_blocked",
            "paper_stage_summary": summary,
            "current_blockers": current_blockers,
            "next_system_action": next_step,
            "next_step": next_step,
            "needs_user_decision": True,
            "needs_physician_decision": True,
            "current_executable_owner_action": dict(current_action),
        }
    )
    return {key: item for key, item in user_visible.items() if item is not None}


def _owner_action_paper_facing_action(action: Mapping[str, Any]) -> dict[str, Any]:
    authority = _mapping_copy(action.get("authority_boundary"))
    return {
        "surface_kind": "paper_mission_paper_facing_action",
        "schema_version": 1,
        "status": "owner_action_ready",
        "source_surface": "paper_mission.next_action",
        "study_id": action.get("study_id"),
        "next_owner": action.get("next_owner") or action.get("owner"),
        "action_type": action.get("action_type"),
        "allowed_actions": action.get("allowed_actions"),
        "work_unit_id": action.get("work_unit_id"),
        "work_unit_fingerprint": action.get("work_unit_fingerprint"),
        "required_delta_kind": action.get("required_delta_kind"),
        "target_surface": action.get("target_surface"),
        "target_surface_specificity": action.get("target_surface_specificity"),
        "paper_facing_delta": action.get("paper_facing_delta"),
        "accepted_answer_shape": action.get("accepted_answer_shape"),
        "route_back": action.get("route_back"),
        "verification": action.get("verification"),
        "next_step": owner_action_next_step(action),
        "authority_boundary": {
            "projection_only": authority.get("projection_only", True),
            "can_write_owner_receipt": False,
            "can_write_typed_blocker": False,
            "can_write_human_gate": False,
            "can_write_current_package": False,
            "can_start_provider_attempt": False,
            "can_claim_submission_ready": False,
            "can_claim_publication_ready": False,
            "can_claim_paper_progress": False,
        },
    }


def _typed_blocker_resolution_status_narration_contract(
    value: object,
    *,
    current_blockers: list[str],
    next_step: str,
    summary: str,
) -> dict[str, Any]:
    contract = _mapping_copy(value)
    stage = _mapping_copy(contract.get("stage"))
    stage["current_stage"] = "owner_action_ready"
    contract["stage"] = stage
    readiness = _mapping_copy(contract.get("readiness"))
    readiness["needs_physician_decision"] = True
    contract["readiness"] = readiness
    contract["current_blockers"] = current_blockers
    contract["latest_update"] = summary
    contract["next_step"] = next_step
    return contract


def _typed_blocker_resolution_successor_envelope(
    *,
    payload: Mapping[str, Any],
    readback: Mapping[str, Any] | None,
    study_id: str,
) -> dict[str, Any] | None:
    resolution = _mapping_copy(readback)
    action = _mapping_copy(resolution.get("next_owner_action"))
    if not action:
        return None
    source_ref = _non_empty_text(resolution.get("source_ref")) or _non_empty_text(
        resolution.get("decision_ref")
    )
    action_type = _non_empty_text(action.get("action_type")) or _first_text(
        action.get("allowed_actions")
    )
    stage_closure = _mapping_copy(payload.get("stage_closure_decision"))
    return compile_next_action_envelope(
        stage_outcome={
            "kind": "next_stage_transition",
            "study_id": _non_empty_text(action.get("study_id")) or study_id,
            "stage_id": _non_empty_text(stage_closure.get("stage_id"))
            or "submission_milestone_candidate",
            "work_unit_id": action.get("work_unit_id"),
            "work_unit_fingerprint": action.get("work_unit_fingerprint"),
            "action_family": "paper.package.submission_minimal",
            "next_action": action_type,
            "decision_signature": action.get("work_unit_fingerprint"),
            "required_input_refs": action.get("acceptance_refs"),
            "paper_facing_delta": action.get("paper_facing_delta"),
            "accepted_answer_shape": action.get("accepted_answer_shape"),
            "route_back": action.get("route_back"),
            "verification": action.get("verification"),
            "executable_owner_route": action.get("executable_owner_route"),
        },
        study_id=_non_empty_text(action.get("study_id")) or study_id,
        stage_id=_non_empty_text(stage_closure.get("stage_id"))
        or "submission_milestone_candidate",
        outcome_ref=source_ref,
        owner_route={
            "next_owner": action.get("next_owner") or "mas_authority_kernel",
            "allowed_actions": action.get("allowed_actions"),
            "action_type": action_type,
            "action_family": "paper.package.submission_minimal",
            "idempotency_key": action.get("work_unit_fingerprint"),
            "paper_facing_delta": action.get("paper_facing_delta"),
            "accepted_answer_shape": action.get("accepted_answer_shape"),
            "route_back": action.get("route_back"),
            "verification": action.get("verification"),
            "executable_owner_route": action.get("executable_owner_route"),
        },
        authority_boundary={
            "projection_only": True,
            "can_claim_stage_complete": False,
            "can_claim_submission_ready": False,
            "can_claim_publication_ready": False,
        },
        diagnostic_refs=[
            {"role": "typed_blocker_resolution", "ref": source_ref}
        ]
        if source_ref is not None
        else [],
    )


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


def _apply_current_work_unit_typed_blocker_user_visible_status(payload: dict[str, Any]) -> dict[str, Any]:
    if _paper_recovery_suppresses_current_work_unit_typed_blocker(payload):
        return payload
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) not in {"typed_blocker", "blocked_current_work_unit"}:
        return payload
    intervention_lane = _mapping_copy(payload.get("intervention_lane"))
    operator_status = _mapping_copy(payload.get("operator_status_card"))
    if _mapping_copy(operator_status.get("no_op_suppression")):
        return payload
    if _non_empty_text(intervention_lane.get("lane_id")) in {
        "runtime_recovery_required",
        "workspace_supervision_gap",
        "quality_floor_blocker",
        "completion_evidence_required",
        "progress_continuation_required",
        "current_owner_action_ready",
        "manual_finishing_fast_lane",
    }:
        return payload
    typed_blocker = _current_work_unit_typed_blocker(current_work_unit)
    if not typed_blocker:
        return payload
    updated = dict(payload)
    reason = _typed_blocker_reason(typed_blocker) or _non_empty_text(current_work_unit.get("status")) or "typed_blocker"
    owner = (
        _non_empty_text(typed_blocker.get("required_next_owner"))
        or _non_empty_text(typed_blocker.get("owner"))
        or _non_empty_text(current_work_unit.get("owner"))
    )
    work_unit_id = _non_empty_text(typed_blocker.get("work_unit_id")) or _non_empty_text(
        current_work_unit.get("work_unit_id")
    )
    action_type = _non_empty_text(typed_blocker.get("action_type")) or _non_empty_text(
        current_work_unit.get("action_type")
    )
    next_step = _typed_blocker_next_step(
        reason=reason,
        owner=owner,
        work_unit_id=work_unit_id,
        action_type=action_type,
    )
    blockers = _typed_blocker_blockers(typed_blocker, reason=reason)
    updated["current_blockers"] = blockers
    updated["next_system_action"] = next_step
    if owner is not None:
        updated["next_owner"] = owner
    user_visible = _mapping_copy(updated.get("user_visible_projection"))
    if user_visible:
        if owner is not None:
            user_visible["owner_resolution_state"] = "ready_for_owner_action"
        else:
            user_visible["owner_resolution_state"] = "blocked_with_typed_owner"
        user_visible["current_blockers"] = blockers
        user_visible["next_system_action"] = next_step
        user_visible["next_step"] = next_step
        user_visible["why_not_progressing"] = reason
        if owner is not None:
            user_visible["next_owner"] = owner
        updated["user_visible_projection"] = user_visible
    status_contract = _mapping_copy(updated.get("status_narration_contract"))
    if status_contract:
        status_contract["current_blockers"] = blockers
        status_contract["next_step"] = next_step
        status_contract["latest_update"] = next_step
        stage = _mapping_copy(status_contract.get("stage"))
        if stage:
            stage["intervention_lane"] = "typed_owner_blocker"
            status_contract["stage"] = stage
        updated["status_narration_contract"] = status_contract
    intervention_lane = _mapping_copy(updated.get("intervention_lane"))
    if intervention_lane:
        intervention_lane.update(
            {
                "lane_id": "typed_owner_blocker",
                "title": "等待当前 typed blocker owner",
                "severity": "critical",
                "summary": next_step,
                "recommended_action_id": "inspect_current_typed_blocker",
                "route_target": owner,
                "route_target_label": owner,
                "route_key_question": reason,
                "route_summary": next_step,
                "work_unit_id": work_unit_id,
                "action_type": action_type,
            }
        )
        updated["intervention_lane"] = {
            key: value for key, value in intervention_lane.items() if value not in (None, "", [], {})
        }
    for key in ("operator_verdict", "recovery_contract"):
        surface = _mapping_copy(updated.get(key))
        if not surface:
            continue
        surface["summary"] = next_step
        if "reason_summary" in surface:
            surface["reason_summary"] = reason
        updated[key] = surface
    operator_status = _mapping_copy(updated.get("operator_status_card"))
    if operator_status:
        operator_status["current_focus"] = next_step
        operator_status["user_visible_verdict"] = next_step
        updated["operator_status_card"] = operator_status
    return updated


def _paper_recovery_suppresses_current_work_unit_typed_blocker(payload: Mapping[str, Any]) -> bool:
    recovery = _mapping_copy(payload.get("paper_recovery_state"))
    suppressed = {
        text
        for item in recovery.get("suppressed_surfaces") or []
        if (text := _non_empty_text(item)) is not None
    }
    return "current_work_unit_typed_blocker" in suppressed


def _current_work_unit_typed_blocker(current_work_unit: Mapping[str, Any]) -> dict[str, Any]:
    state = _mapping_copy(current_work_unit.get("state"))
    typed_blocker = _mapping_copy(state.get("typed_blocker")) or _mapping_copy(current_work_unit.get("typed_blocker"))
    if _non_empty_text(current_work_unit.get("status")) != "typed_blocker" and not typed_blocker:
        return {}
    if not typed_blocker:
        typed_blocker = {
            "blocker_type": _non_empty_text(state.get("blocker_type")),
            "blocker_id": _non_empty_text(state.get("blocker_id")),
            "blocked_reason": _non_empty_text(state.get("blocked_reason")),
        }
    for key in ("owner", "action_type", "work_unit_id", "work_unit_fingerprint"):
        typed_blocker.setdefault(key, _non_empty_text(current_work_unit.get(key)))
    if _non_empty_text(current_work_unit.get("status")) == "blocked_current_work_unit" and _generic_unresolved_typed_blocker(
        typed_blocker=typed_blocker,
        source=_non_empty_text(state.get("source")),
    ):
        return {}
    return {key: value for key, value in typed_blocker.items() if value not in (None, "", [], {})}


def _generic_unresolved_typed_blocker(*, typed_blocker: Mapping[str, Any], source: str | None) -> bool:
    if source != "blocked_current_work_unit":
        return False
    if _typed_blocker_reason(typed_blocker) != "current_work_unit_unresolved":
        return False
    identity_fields = (
        "action_type",
        "work_unit_id",
        "work_unit_fingerprint",
        "action_fingerprint",
        "blocker_id",
        "latest_owner_answer_ref",
        "typed_blocker_ref",
        "owner_receipt_ref",
    )
    return not any(_non_empty_text(typed_blocker.get(key)) is not None for key in identity_fields)


def _typed_blocker_blockers(typed_blocker: Mapping[str, Any], *, reason: str) -> list[str]:
    values: list[str] = [reason]
    for item in typed_blocker.get("remaining_blockers") or []:
        if text := _non_empty_text(item):
            values.append(text)
    for key in ("summary", "required_input", "source_ref"):
        if text := _non_empty_text(typed_blocker.get(key)):
            values.append(text)
    return list(dict.fromkeys(values))[:8]


def _typed_blocker_next_step(
    *,
    reason: str,
    owner: str | None,
    work_unit_id: str | None,
    action_type: str | None,
) -> str:
    owner_text = owner or "当前 owner"
    subject = f" work unit {work_unit_id}" if work_unit_id is not None else ""
    action = f" / {action_type}" if action_type is not None else ""
    return f"等待 {owner_text} 处理当前 typed blocker：{reason}{subject}{action}。"
