from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from med_autoscience.profiles import WorkspaceProfile


def _stale_time_to_event_grouped_payload_blocker(
    *,
    paper_root: Path,
) -> dict[str, Any]:
    payload_path = Path(paper_root) / "time_to_event_grouped_inputs.json"
    return {
        "status": "failed",
        "blocker": "stale_legacy_time_to_event_grouped_payload",
        "payload_path": str(payload_path),
        "blocking_artifact_refs": [
            {
                "blocker": "stale_legacy_time_to_event_grouped_payload",
                "artifact_path": str(payload_path),
                "artifact_role": "display_input_payload",
                "failure_reason": (
                    "time_to_event_risk_group_summary payload contains cumulative-incidence groups; "
                    "current display truth must be rematerialized by the time-to-event direct-migration owner"
                ),
                "required_owner": "time_to_event_direct_migration",
                "terminal_state": "gate_needs_specificity",
            }
        ],
        "terminal_state": "gate_needs_specificity",
        "next_owner": "time_to_event_direct_migration",
    }


def _append_repair_paper_live_paths_unit(
    *,
    repair_units: list[Any],
    repair_unit_cls: type,
    profile: WorkspaceProfile,
    quest_id: str,
    paper_root: Path,
    current_workspace_root: Path,
    repair_paper_live_paths: Callable[..., dict[str, Any]],
) -> None:
    repair_units.append(
        repair_unit_cls(
            unit_id="repair_paper_live_paths",
            label="Repair runtime-owned paper live paths before publication-surface replay",
            parallel_safe=True,
            run=lambda: repair_paper_live_paths(
                profile=profile,
                quest_id=quest_id,
                workspace_root=paper_root.parent,
                current_workspace_root=current_workspace_root,
            ),
        )
    )


def _append_workspace_display_script_unit(
    *,
    repair_units: list[Any],
    repair_unit_cls: type,
    paper_root: Path,
    depends_on: tuple[str, ...] = (),
    label: str,
    run_workspace_display_repair_script: Callable[..., dict[str, Any]],
) -> None:
    repair_units.append(
        repair_unit_cls(
            unit_id="workspace_display_repair_script",
            label=label,
            parallel_safe=True,
            depends_on=depends_on,
            run=lambda: run_workspace_display_repair_script(paper_root=paper_root),
        )
    )


def _append_display_materialization_units(
    *,
    repair_units: list[Any],
    repair_unit_cls: type,
    profile: WorkspaceProfile,
    study_root: Path,
    paper_root: Path,
    existing_dependency_ids: Callable[..., tuple[str, ...]],
    materialize_display_surface: Callable[..., dict[str, Any]],
    publication_shell_surface_needs_sync: Callable[..., bool],
    time_to_event_direct_migration_display_inputs_need_refresh: Callable[..., bool],
    stale_time_to_event_grouped_payloads_need_rematerialization: Callable[..., bool],
    time_to_event_risk_group_surface_present: Callable[..., bool],
    gate_clearing_batch_transportability: Any,
    publication_shell_sync: Any,
    time_to_event_direct_migration: Any,
) -> None:
    if gate_clearing_batch_transportability.transportability_reporting_surface_needs_sync(
        study_root=study_root,
        paper_root=paper_root,
        profile=profile,
    ):
        repair_units.append(
            repair_unit_cls(
                unit_id="sync_transportability_reporting_surface",
                label="Sync transportability reporting display contract before surface materialization",
                parallel_safe=True,
                depends_on=existing_dependency_ids(repair_units, "repair_paper_live_paths"),
                run=lambda: gate_clearing_batch_transportability.sync_transportability_reporting_surface(
                    study_root=study_root,
                    paper_root=paper_root,
                    profile=profile,
                ),
            )
        )
    if time_to_event_direct_migration_display_inputs_need_refresh(paper_root=paper_root):
        repair_units.append(
            repair_unit_cls(
                unit_id="time_to_event_direct_migration",
                label="Refresh canonical time-to-event direct-migration display inputs before surface materialization",
                parallel_safe=True,
                depends_on=existing_dependency_ids(
                    repair_units,
                    "repair_paper_live_paths",
                    "sync_transportability_reporting_surface",
                ),
                run=lambda: time_to_event_direct_migration.run_time_to_event_direct_migration(
                    study_root=study_root,
                    paper_root=paper_root,
                ),
            )
        )
    if _stale_time_to_event_grouped_payloads_need_rematerialization(
        paper_root=paper_root,
        repair_units=repair_units,
        stale_time_to_event_grouped_payloads_need_rematerialization=stale_time_to_event_grouped_payloads_need_rematerialization,
        time_to_event_risk_group_surface_present=time_to_event_risk_group_surface_present,
    ):
        repair_units.append(
            repair_unit_cls(
                unit_id="stale_time_to_event_grouped_payload_blocker",
                label="Block stale time-to-event grouped display payload until canonical rematerialization",
                parallel_safe=False,
                depends_on=existing_dependency_ids(
                    repair_units,
                    "repair_paper_live_paths",
                    "sync_transportability_reporting_surface",
                    "time_to_event_direct_migration",
                ),
                run=lambda: _stale_time_to_event_grouped_payload_blocker(paper_root=paper_root),
            )
        )
    if publication_shell_surface_needs_sync(study_root=study_root, paper_root=paper_root):
        repair_units.append(
            repair_unit_cls(
                unit_id="sync_publication_shell_surface",
                label="Sync publication shell table inputs before surface materialization",
                parallel_safe=True,
                depends_on=existing_dependency_ids(repair_units, "repair_paper_live_paths"),
                run=lambda: publication_shell_sync.run_publication_shell_sync(
                    study_root=study_root,
                    paper_root=paper_root,
                ),
            )
        )
    repair_units.append(
        repair_unit_cls(
            unit_id="materialize_display_surface",
            label="Refresh display catalogs and generated paper-facing exports",
            parallel_safe=True,
            depends_on=existing_dependency_ids(
                repair_units,
                "repair_paper_live_paths",
                "sync_transportability_reporting_surface",
                "time_to_event_direct_migration",
                "stale_time_to_event_grouped_payload_blocker",
                "sync_publication_shell_surface",
            ),
            run=lambda: materialize_display_surface(paper_root=paper_root),
        )
    )


def _stale_time_to_event_grouped_payloads_need_rematerialization(
    *,
    paper_root: Path,
    repair_units: list[Any],
    stale_time_to_event_grouped_payloads_need_rematerialization: Callable[..., bool],
    time_to_event_risk_group_surface_present: Callable[..., bool],
) -> bool:
    if any(unit.unit_id == "time_to_event_direct_migration" for unit in repair_units):
        return False
    return stale_time_to_event_grouped_payloads_need_rematerialization(paper_root=paper_root) or (
        time_to_event_risk_group_surface_present(paper_root=paper_root)
        and any(unit.unit_id == "sync_transportability_reporting_surface" for unit in repair_units)
    )


def build_gate_clearing_repair_units(
    *,
    repair_unit_cls: type,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    quest_id: str,
    paper_root: Path,
    current_workspace_root: Path,
    mapping_path: Path | None,
    mapping_payload: dict[str, Any],
    gate_report: dict[str, Any],
    authority_settle_delivery_redrive_requested: bool,
    bundle_stage_repair: bool,
    direct_submission_delivery_sync_requested: bool,
    submission_minimal_refresh_requested: bool,
    selected_work_unit_id: str | None,
    controller_decision_work_unit_id: str | None,
    resolved_route_context: dict[str, Any] | None,
    existing_dependency_ids: Callable[..., tuple[str, ...]],
    freeze_scientific_anchor_fields: Callable[..., dict[str, Any]],
    repair_paper_live_paths: Callable[..., dict[str, Any]],
    run_workspace_display_repair_script: Callable[..., dict[str, Any]],
    materialize_display_surface: Callable[..., dict[str, Any]],
    publication_shell_surface_needs_sync: Callable[..., bool],
    time_to_event_direct_migration_display_inputs_need_refresh: Callable[..., bool],
    stale_time_to_event_grouped_payloads_need_rematerialization: Callable[..., bool],
    time_to_event_risk_group_surface_present: Callable[..., bool],
    sync_submission_minimal_delivery: Callable[..., dict[str, Any]],
    create_submission_minimal_package: Callable[..., dict[str, Any]],
    route_bound: Callable[..., Callable[..., dict[str, Any]]],
    route_call: Callable[..., dict[str, Any]],
    path_fingerprints: Callable[..., list[dict[str, Any]]],
    medical_surface_display_repair_requested: Callable[..., bool],
    gate_clearing_batch_submission: Any,
    gate_clearing_batch_transportability: Any,
    publication_shell_sync: Any,
    time_to_event_direct_migration: Any,
    current_package_authority_settle_window_ns: int,
) -> list[Any]:
    repair_units: list[Any] = []
    if mapping_payload and mapping_path is not None:
        repair_units.append(
            repair_unit_cls(
                unit_id="freeze_scientific_anchor_fields",
                label="Freeze scientific-anchor fields from the latest bounded-analysis output",
                parallel_safe=True,
                run=lambda: freeze_scientific_anchor_fields(
                    study_root=study_root,
                    study_id=study_id,
                    profile=profile,
                    mapping_path=mapping_path,
                ),
            )
        )
    display_repair_script_path = paper_root / "build" / "generate_display_exports.py"
    if (
        not authority_settle_delivery_redrive_requested
        and medical_surface_display_repair_requested(
            gate_report,
            submission_minimal_repair_gate_blockers=gate_clearing_batch_submission.SUBMISSION_MINIMAL_REPAIR_GATE_BLOCKERS,
        )
    ):
        _append_repair_paper_live_paths_unit(
            repair_units=repair_units,
            repair_unit_cls=repair_unit_cls,
            profile=profile,
            quest_id=quest_id,
            paper_root=paper_root,
            current_workspace_root=current_workspace_root,
            repair_paper_live_paths=repair_paper_live_paths,
        )
        if display_repair_script_path.exists():
            _append_workspace_display_script_unit(
                repair_units=repair_units,
                repair_unit_cls=repair_unit_cls,
                paper_root=paper_root,
                depends_on=existing_dependency_ids(repair_units, "repair_paper_live_paths"),
                label="Run the workspace-authored display repair script before gate replay",
                run_workspace_display_repair_script=run_workspace_display_repair_script,
            )
        else:
            _append_display_materialization_units(
                repair_units=repair_units,
                repair_unit_cls=repair_unit_cls,
                profile=profile,
                study_root=study_root,
                paper_root=paper_root,
                existing_dependency_ids=existing_dependency_ids,
                materialize_display_surface=materialize_display_surface,
                publication_shell_surface_needs_sync=publication_shell_surface_needs_sync,
                time_to_event_direct_migration_display_inputs_need_refresh=(
                    time_to_event_direct_migration_display_inputs_need_refresh
                ),
                stale_time_to_event_grouped_payloads_need_rematerialization=(
                    stale_time_to_event_grouped_payloads_need_rematerialization
                ),
                time_to_event_risk_group_surface_present=time_to_event_risk_group_surface_present,
                gate_clearing_batch_transportability=gate_clearing_batch_transportability,
                publication_shell_sync=publication_shell_sync,
                time_to_event_direct_migration=time_to_event_direct_migration,
            )
    elif not authority_settle_delivery_redrive_requested and bundle_stage_repair and display_repair_script_path.exists():
        _append_workspace_display_script_unit(
            repair_units=repair_units,
            repair_unit_cls=repair_unit_cls,
            paper_root=paper_root,
            label="Run the workspace-authored display repair script before bundle-stage gate replay",
            run_workspace_display_repair_script=run_workspace_display_repair_script,
        )
    if direct_submission_delivery_sync_requested:
        repair_units.append(
            repair_unit_cls(
                unit_id="sync_submission_minimal_delivery",
                label="Refresh the study-owned submission-minimal delivery mirror before gate replay",
                parallel_safe=True,
                depends_on=existing_dependency_ids(
                    repair_units,
                    "repair_paper_live_paths",
                    "workspace_display_repair_script",
                    "materialize_display_surface",
                ),
                run=lambda: gate_clearing_batch_submission.sync_submission_minimal_delivery_after_settle(
                    paper_root=paper_root,
                    profile=profile,
                    sync_submission_minimal_delivery=route_bound(
                        function=sync_submission_minimal_delivery,
                        control_plane_route_context=resolved_route_context,
                    ),
                    path_fingerprints=path_fingerprints,
                    settle_window_ns=current_package_authority_settle_window_ns,
                ),
            )
        )
    if bundle_stage_repair and (
        submission_minimal_refresh_requested or selected_work_unit_id == "submission_authority_sync_closure"
    ):
        submission_refresh_dependencies = (
            ()
            if (
                selected_work_unit_id in {"submission_minimal_refresh", "submission_authority_sync_closure"}
                and controller_decision_work_unit_id in {"submission_minimal_refresh", "submission_authority_sync_closure"}
            )
            else existing_dependency_ids(
                repair_units,
                "repair_paper_live_paths",
                "workspace_display_repair_script",
                "materialize_display_surface",
            )
        )
        repair_units.append(
            repair_unit_cls(
                unit_id="create_submission_minimal_package",
                label="Regenerate submission-minimal assets before gate replay",
                parallel_safe=False,
                depends_on=submission_refresh_dependencies,
                run=lambda: route_call(
                    create_submission_minimal_package,
                    paper_root=paper_root,
                    profile=profile,
                    control_plane_route_context=resolved_route_context,
                ),
            )
        )
    return repair_units
