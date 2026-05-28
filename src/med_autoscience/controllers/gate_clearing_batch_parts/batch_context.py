from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from med_autoscience.controllers.gate_clearing_batch_work_units import (
    PUBLICATION_WORK_UNIT_REPAIR_IDS,
    UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS,
)
from med_autoscience.profiles import WorkspaceProfile


GATE_CLEARING_ROUTE_WORK_UNIT_IDS = frozenset(PUBLICATION_WORK_UNIT_REPAIR_IDS) | {
    "publication_gate_replay",
}


@dataclass(frozen=True)
class GateClearingBatchContext:
    resolved_route_context: dict[str, Any] | None
    resolved_study_root: Path
    quest_root: Path
    gate_state: Any
    gate_report: dict[str, Any]
    publication_eval_payload: dict[str, Any]
    latest_batch: dict[str, Any]
    current_eval_id: str
    controller_decision_work_unit: dict[str, Any] | None
    paper_root: Path | None
    current_workspace_root: Path | None
    mapping_path: Path | None
    mapping_payload: dict[str, Any]
    gate_blockers: set[str]
    bundle_stage_repair: bool
    study_delivery_status: str
    submission_minimal_refresh_requested: bool
    direct_submission_delivery_sync_requested: bool
    authority_settle_delivery_redrive_requested: bool
    work_unit_selection: dict[str, Any] | None


def build_gate_clearing_batch_context(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    quest_id: str,
    authority_route_context: dict[str, Any] | None,
    route_context: dict[str, Any] | None,
    quest_root_for_profile: Callable[..., Path],
    publication_gate_controller: Any,
    read_publication_eval_latest_fn: Callable[..., dict[str, Any]],
    latest_batch_record: Callable[..., dict[str, Any]],
    latest_batch_closed_for_eval: Callable[[dict[str, Any], str | None], bool],
    current_workspace_root_fn: Callable[..., Path],
    eligible_mapping_payload: Callable[..., tuple[Path | None, dict[str, Any]]],
    gate_blockers_fn: Callable[[dict[str, Any]], set[str]],
    submission_controller: Any,
    authority_redrive_controller: Any,
    study_delivery_sync_controller: Any,
    currentness_controller: Any,
) -> GateClearingBatchContext:
    resolved_route_context = authority_route_context or route_context
    resolved_study_root = Path(study_root).expanduser().resolve()
    quest_root = quest_root_for_profile(profile, quest_id=quest_id)
    gate_state = publication_gate_controller.build_gate_state(quest_root)
    gate_report = publication_gate_controller.build_gate_report(gate_state)
    publication_eval_payload = read_publication_eval_latest_fn(study_root=resolved_study_root)
    latest_batch = latest_batch_record(study_root=resolved_study_root)
    current_eval_id = str(publication_eval_payload.get("eval_id") or "").strip()
    controller_decision_work_unit = currentness_controller.controller_decision_publication_work_unit(
        study_root=resolved_study_root,
        study_id=study_id,
        quest_id=quest_id,
        source_eval_id=current_eval_id,
    )
    route_context_work_unit = _controller_route_context_publication_work_unit(
        resolved_route_context,
        source_eval_id=current_eval_id,
    )
    if route_context_work_unit is not None:
        controller_decision_work_unit = route_context_work_unit
    if latest_batch_closed_for_eval(latest_batch, current_eval_id):
        return GateClearingBatchContext(
            resolved_route_context=resolved_route_context,
            resolved_study_root=resolved_study_root,
            quest_root=quest_root,
            gate_state=gate_state,
            gate_report=gate_report,
            publication_eval_payload=publication_eval_payload,
            latest_batch=latest_batch,
            current_eval_id=current_eval_id,
            controller_decision_work_unit=controller_decision_work_unit,
            paper_root=None,
            current_workspace_root=None,
            mapping_path=None,
            mapping_payload={},
            gate_blockers=set(),
            bundle_stage_repair=False,
            study_delivery_status="",
            submission_minimal_refresh_requested=False,
            direct_submission_delivery_sync_requested=False,
            authority_settle_delivery_redrive_requested=False,
            work_unit_selection=None,
        )

    paper_root = gate_state.paper_root
    if paper_root is None:
        return GateClearingBatchContext(
            resolved_route_context=resolved_route_context,
            resolved_study_root=resolved_study_root,
            quest_root=quest_root,
            gate_state=gate_state,
            gate_report=gate_report,
            publication_eval_payload=publication_eval_payload,
            latest_batch=latest_batch,
            current_eval_id=current_eval_id,
            controller_decision_work_unit=controller_decision_work_unit,
            paper_root=None,
            current_workspace_root=None,
            mapping_path=None,
            mapping_payload={},
            gate_blockers=set(),
            bundle_stage_repair=False,
            study_delivery_status="",
            submission_minimal_refresh_requested=False,
            direct_submission_delivery_sync_requested=False,
            authority_settle_delivery_redrive_requested=False,
            work_unit_selection=None,
        )

    current_workspace_root = current_workspace_root_fn(quest_root=quest_root, default=paper_root.parent)
    mapping_path, mapping_payload = eligible_mapping_payload(quest_root=quest_root, study_root=resolved_study_root)
    gate_blockers = gate_blockers_fn(gate_report)
    bundle_stage_repair = submission_controller.bundle_stage_repair_requested(gate_report=gate_report)
    study_delivery_status = submission_controller.study_delivery_status(gate_report)
    submission_minimal_refresh_requested = submission_controller.submission_minimal_refresh_requested(
        gate_report=gate_report
    )
    can_sync_study_delivery = study_delivery_sync_controller.can_sync_study_delivery(paper_root=paper_root)
    direct_submission_delivery_sync_requested = (
        bundle_stage_repair
        and not submission_minimal_refresh_requested
        and submission_controller.direct_submission_delivery_sync_requested(gate_report=gate_report)
        and can_sync_study_delivery
    )
    authority_settle_delivery_redrive_requested = authority_redrive_controller.authority_settle_delivery_redrive_requested(
        latest_batch=latest_batch,
        study_delivery_status=study_delivery_status,
        bundle_stage_repair=bundle_stage_repair,
        submission_minimal_refresh_requested=submission_minimal_refresh_requested,
        submission_minimal_core_outputs_missing=submission_controller.submission_minimal_core_outputs_missing(
            gate_report
        ),
        can_sync_study_delivery=can_sync_study_delivery,
    )
    if authority_settle_delivery_redrive_requested:
        direct_submission_delivery_sync_requested = True
        submission_minimal_refresh_requested = False
    work_unit_selection = currentness_controller.publication_work_unit_selection(
        publication_eval_payload=publication_eval_payload,
        latest_batch=latest_batch,
        gate_report=gate_report,
        authority_settle_delivery_redrive_requested=authority_settle_delivery_redrive_requested,
        direct_submission_delivery_sync_requested=direct_submission_delivery_sync_requested,
        controller_decision_work_unit=controller_decision_work_unit,
    )
    return GateClearingBatchContext(
        resolved_route_context=resolved_route_context,
        resolved_study_root=resolved_study_root,
        quest_root=quest_root,
        gate_state=gate_state,
        gate_report=gate_report,
        publication_eval_payload=publication_eval_payload,
        latest_batch=latest_batch,
        current_eval_id=current_eval_id,
        controller_decision_work_unit=controller_decision_work_unit,
        paper_root=paper_root,
        current_workspace_root=current_workspace_root,
        mapping_path=mapping_path,
        mapping_payload=mapping_payload,
        gate_blockers=gate_blockers,
        bundle_stage_repair=bundle_stage_repair,
        study_delivery_status=study_delivery_status,
        submission_minimal_refresh_requested=submission_minimal_refresh_requested,
        direct_submission_delivery_sync_requested=direct_submission_delivery_sync_requested,
        authority_settle_delivery_redrive_requested=authority_settle_delivery_redrive_requested,
        work_unit_selection=work_unit_selection,
    )


def _controller_route_context_publication_work_unit(
    route_context: dict[str, Any] | None,
    *,
    source_eval_id: str | None,
) -> dict[str, str] | None:
    if not isinstance(route_context, dict):
        return None
    controller_route_context = route_context.get("controller_route_context")
    if not isinstance(controller_route_context, dict):
        return None
    if bool(controller_route_context.get("requires_human_confirmation")):
        return None
    control_surface = str(controller_route_context.get("control_surface") or "").strip()
    controller_action_type = str(controller_route_context.get("controller_action_type") or "").strip()
    if (
        control_surface,
        controller_action_type,
    ) not in {
        ("quality_repair_batch", "run_quality_repair_batch"),
        ("gate_clearing_batch", "run_gate_clearing_batch"),
    }:
        return None
    context_eval_id = str(controller_route_context.get("source_eval_id") or "").strip()
    if source_eval_id and context_eval_id and context_eval_id != source_eval_id:
        return None
    work_unit_id = str(controller_route_context.get("work_unit_id") or "").strip()
    if control_surface == "quality_repair_batch" and work_unit_id not in UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS:
        return None
    if control_surface == "gate_clearing_batch" and work_unit_id not in GATE_CLEARING_ROUTE_WORK_UNIT_IDS:
        return None
    return {"unit_id": work_unit_id}
