from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any, Callable

from med_autoscience.publication_eval_latest import read_publication_eval_latest
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.controllers.gate_clearing_batch_blockers import (
    medical_surface_display_repair_requested,
    repairable_medical_surface,
)
from med_autoscience.controllers.gate_clearing_batch_fingerprints import (
    globbed_path_fingerprints as _globbed_path_fingerprints,
    path_fingerprint as _path_fingerprint,
    path_fingerprints as _path_fingerprints,
)
from med_autoscience.controllers import gate_clearing_batch_package_freshness
from med_autoscience.controllers import gate_clearing_batch_submission
from med_autoscience.controllers import gate_clearing_batch_scheduler
from med_autoscience.controllers import gate_clearing_batch_execution
from med_autoscience.controllers import gate_clearing_batch_currentness
from med_autoscience.controllers import gate_clearing_batch_repair_fingerprints
from med_autoscience.controllers import gate_clearing_batch_replay_closure
from med_autoscience.controllers import publication_work_units
from med_autoscience.controllers import publication_work_unit_lifecycle
from med_autoscience.controllers import gate_clearing_batch_transportability
from med_autoscience.controllers import gate_clearing_batch_authority_redrive
from med_autoscience.controllers import publication_shell_sync
from med_autoscience.controllers.gate_clearing_batch_parts import display_refresh
from med_autoscience.controllers.gate_clearing_batch_parts import execution_helpers
from med_autoscience.controllers.gate_clearing_batch_parts import io_utils
from med_autoscience.controllers.gate_clearing_batch_parts import path_selection
from med_autoscience.controllers.gate_clearing_batch_parts import runtime_paths
from med_autoscience.controllers.gate_clearing_batch_parts import scientific_anchor
from med_autoscience.controllers.gate_clearing_batch_parts import startup_freshness
from med_autoscience.controllers.gate_clearing_batch_parts import submission_delivery
from med_autoscience.controllers.gate_clearing_batch_execution import GateClearingRepairUnit
from med_autoscience.controllers.gate_clearing_batch_work_units import (
    filter_repair_units_for_publication_work_unit,
)
from med_autoscience.controllers.control_plane_route_context_call import call_with_control_plane_route_context as _route_call
from med_autoscience.controllers.gate_clearing_batch_write_routes import route_bound_call as _route_bound
from med_autoscience.controllers.gate_clearing_batch_write_routes import create_submission_minimal_package_with_route
from med_autoscience.controllers.gate_clearing_batch_write_routes import sync_submission_minimal_delivery_with_route


SCHEMA_VERSION = 1
STABLE_GATE_CLEARING_BATCH_RELATIVE_PATH = Path("artifacts/controller/gate_clearing_batch/latest.json")
CURRENT_PACKAGE_AUTHORITY_SETTLE_WINDOW_NS = 5_000_000_000


def _load_controller(module_name: str):
    return import_module(f"med_autoscience.controllers.{module_name}")


class _LazyModuleProxy:
    def __init__(self, loader: Callable[[], Any]) -> None:
        object.__setattr__(self, "_loader", loader)
        object.__setattr__(self, "_module", None)

    def _resolve(self):
        module = object.__getattribute__(self, "_module")
        if module is None:
            module = object.__getattribute__(self, "_loader")()
            object.__setattr__(self, "_module", module)
        return module

    def __getattr__(self, name: str) -> Any:
        return getattr(self._resolve(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            object.__setattr__(self, name, value)
            return
        setattr(self._resolve(), name, value)


display_surface_materialization = _LazyModuleProxy(lambda: _load_controller("display_surface_materialization"))
publication_gate = _LazyModuleProxy(lambda: _load_controller("publication_gate"))
study_delivery_sync = _LazyModuleProxy(lambda: _load_controller("study_delivery_sync"))
submission_minimal = _LazyModuleProxy(lambda: _load_controller("submission_minimal"))
study_runtime_router = _LazyModuleProxy(lambda: _load_controller("study_runtime_router"))
time_to_event_direct_migration = _LazyModuleProxy(lambda: _load_controller("time_to_event_direct_migration"))


def stable_gate_clearing_batch_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / STABLE_GATE_CLEARING_BATCH_RELATIVE_PATH


_read_json = io_utils.read_json
_write_json = io_utils.write_json


_clock_snapshot = publication_work_unit_lifecycle.clock_snapshot


_parse_json_object_from_cli_stdout = execution_helpers.parse_json_object_from_cli_stdout
_non_empty_text = io_utils.non_empty_text
_string_list = io_utils.string_list


def _unit_blocking_artifact_refs(unit_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for item in unit_results:
        value = item.get("blocking_artifact_refs")
        if not isinstance(value, list):
            continue
        for ref in value:
            if not isinstance(ref, dict):
                continue
            if ref not in refs:
                refs.append(ref)
    return refs


_quest_root = runtime_paths.quest_root


resolve_profile_for_study_root = runtime_paths.resolve_profile_for_study_root


_current_workspace_root = runtime_paths.current_workspace_root


def _candidate_values_include_root(
    *,
    workspace_root: Path,
    candidate_values: list[object],
    root: Path,
) -> bool:
    return path_selection.candidate_values_include_root(
        workspace_root=workspace_root,
        candidate_values=candidate_values,
        root=root,
        submission_minimal_controller=submission_minimal,
    )


def _catalog_asset_fingerprints(
    *,
    workspace_root: Path,
    catalog_payload: dict[str, Any],
    item_key: str,
    resolve_source_paths: Callable[[dict[str, Any]], list[str]],
    limit: int = 128,
) -> list[dict[str, Any]]:
    return gate_clearing_batch_repair_fingerprints.catalog_asset_fingerprints(
        workspace_root=workspace_root,
        catalog_payload=catalog_payload,
        item_key=item_key,
        resolve_source_paths=resolve_source_paths,
        submission_minimal_controller=submission_minimal,
        path_fingerprint=_path_fingerprint,
        limit=limit,
    )


def _submission_minimal_fingerprint_payload(
    *,
    paper_root: Path,
    gate_report: dict[str, Any],
    profile: WorkspaceProfile | None,
) -> dict[str, Any]:
    return gate_clearing_batch_repair_fingerprints.submission_minimal_fingerprint_payload(
        paper_root=paper_root,
        gate_report=gate_report,
        profile=profile,
        submission_minimal_controller=submission_minimal,
        path_fingerprint=_path_fingerprint,
        path_fingerprints=_path_fingerprints,
    )


def _repair_unit_fingerprint(
    *,
    unit_id: str,
    paper_root: Path,
    gate_report: dict[str, Any],
    profile: WorkspaceProfile | None = None,
) -> str | None:
    return gate_clearing_batch_repair_fingerprints.repair_unit_fingerprint(
        unit_id=unit_id,
        paper_root=paper_root,
        gate_report=gate_report,
        profile=profile,
        submission_minimal_controller=submission_minimal,
        path_fingerprint=_path_fingerprint,
        path_fingerprints=_path_fingerprints,
        globbed_path_fingerprints=_globbed_path_fingerprints,
    )


def _latest_unit_result(latest_batch: dict[str, Any], *, unit_id: str) -> dict[str, Any] | None:
    return gate_clearing_batch_execution.latest_unit_result(latest_batch, unit_id=unit_id)


def _latest_unit_status(latest_batch: dict[str, Any], *, unit_id: str) -> str | None:
    return gate_clearing_batch_execution.latest_unit_status(latest_batch, unit_id=unit_id)


def _unit_status_is_success(status: str | None) -> bool:
    return gate_clearing_batch_execution.unit_status_is_success(status)


def _latest_unit_success_status(latest_batch: dict[str, Any], *, unit_id: str) -> str | None:
    return gate_clearing_batch_execution.latest_unit_success_status(latest_batch, unit_id=unit_id)


def _latest_unit_fingerprint(latest_batch: dict[str, Any], *, unit_id: str) -> str | None:
    return gate_clearing_batch_execution.latest_unit_fingerprint(latest_batch, unit_id=unit_id)


def _can_skip_repair_unit(
    latest_batch: dict[str, Any],
    *,
    unit_id: str,
    unit_fingerprint: str | None,
) -> bool:
    return gate_clearing_batch_execution.can_skip_repair_unit(
        latest_batch,
        unit_id=unit_id,
        unit_fingerprint=unit_fingerprint,
    )


def _unit_status_blocks_dependents(status: str | None) -> bool:
    return gate_clearing_batch_execution.unit_status_blocks_dependents(status)


def _existing_dependency_ids(
    repair_units: list[GateClearingRepairUnit],
    *candidate_unit_ids: str,
) -> tuple[str, ...]:
    return gate_clearing_batch_execution.existing_dependency_ids(repair_units, *candidate_unit_ids)


def _run_repair_unit(
    *,
    unit: GateClearingRepairUnit,
    latest_batch: dict[str, Any],
    paper_root: Path,
    gate_report: dict[str, Any],
    profile: WorkspaceProfile,
) -> tuple[dict[str, Any], str | None]:
    return gate_clearing_batch_execution.run_repair_unit(
        unit=unit,
        latest_batch=latest_batch,
        paper_root=paper_root,
        gate_report=gate_report,
        profile=profile,
        repair_unit_fingerprint=_repair_unit_fingerprint,
        clock_snapshot=_clock_snapshot,
    )


def _execute_repair_units(
    *,
    repair_units: list[GateClearingRepairUnit],
    latest_batch: dict[str, Any],
    paper_root: Path,
    gate_report: dict[str, Any],
    profile: WorkspaceProfile,
) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, int]]:
    return gate_clearing_batch_execution.execute_repair_units(
        repair_units=repair_units,
        latest_batch=latest_batch,
        paper_root=paper_root,
        gate_report=gate_report,
        profile=profile,
        repair_unit_fingerprint=_repair_unit_fingerprint,
        clock_snapshot=_clock_snapshot,
    )


def _reuse_embedded_submission_delivery_sync(
    *,
    create_submission_result: dict[str, Any] | None,
) -> dict[str, Any] | None:
    return gate_clearing_batch_execution.reuse_embedded_submission_delivery_sync(
        create_submission_result=create_submission_result,
    )


def _latest_batch_record(*, study_root: Path) -> dict[str, Any]:
    return _read_json(stable_gate_clearing_batch_path(study_root=study_root))


def _latest_batch_closed_for_eval(latest_batch: dict[str, Any], current_eval_id: str | None) -> bool:
    return gate_clearing_batch_currentness.batch_closed_for_source_eval(latest_batch, source_eval_id=current_eval_id)


def _recommended_action_by_type(
    *,
    publication_eval_payload: dict[str, Any],
    action_types: frozenset[str],
) -> dict[str, Any] | None:
    recommended_actions = publication_eval_payload.get("recommended_actions") or []
    if not isinstance(recommended_actions, list):
        return None
    return next(
        (
            dict(action)
            for action in recommended_actions
            if isinstance(action, dict) and str(action.get("action_type") or "").strip() in action_types
        ),
        None,
    )


def _gate_blockers(gate_report: dict[str, Any]) -> set[str]:
    return {
        str(item or "").strip()
        for item in (gate_report.get("blockers") or [])
        if str(item or "").strip()
    }


def _eligible_mapping_payload(*, quest_root: Path, study_root: Path) -> tuple[Path | None, dict[str, Any]]:
    return scientific_anchor.eligible_mapping_payload(quest_root=quest_root, study_root=study_root)


def build_gate_clearing_batch_recommended_action(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    quest_id: str,
    publication_eval_payload: dict[str, Any],
    gate_report: dict[str, Any],
    prefer_startup_freshness_work_unit: bool = False,
) -> dict[str, Any] | None:
    verdict = publication_eval_payload.get("verdict")
    if not isinstance(verdict, dict) or str(verdict.get("overall_verdict") or "").strip() != "blocked":
        return None
    bounded_analysis_action = _recommended_action_by_type(
        publication_eval_payload=publication_eval_payload,
        action_types=frozenset({"bounded_analysis"}),
    )
    same_line_action = _recommended_action_by_type(
        publication_eval_payload=publication_eval_payload,
        action_types=frozenset({"continue_same_line", "route_back_same_line"}),
    )
    controller_return_action = _recommended_action_by_type(
        publication_eval_payload=publication_eval_payload,
        action_types=frozenset({"return_to_controller"}),
    )

    gate_status = str(gate_report.get("status") or "").strip()
    if gate_status != "blocked":
        return None

    gate_blockers = _gate_blockers(gate_report)
    if not gate_blockers:
        return None
    publication_work_unit_payload = publication_work_units.derive_publication_work_units(gate_report)
    if prefer_startup_freshness_work_unit:
        publication_work_unit_payload = startup_freshness.apply_startup_freshness_work_unit(
            publication_work_unit_payload=publication_work_unit_payload,
            submission_minimal_refresh_requested=gate_clearing_batch_submission.submission_minimal_refresh_requested(
                gate_report=gate_report
            ),
        )
    if (
        publication_work_unit_payload.get("actionability_status") == "blocked_by_non_actionable_gate"
        and not prefer_startup_freshness_work_unit
    ):
        return None
    current_required_action = str(gate_report.get("current_required_action") or "").strip()

    repairable_surface = repairable_medical_surface(gate_report)
    stale_delivery = "stale_study_delivery_mirror" in gate_blockers
    bundle_stage_repair = gate_clearing_batch_submission.bundle_stage_repair_requested(gate_report=gate_report)
    quest_root = _quest_root(profile, quest_id=quest_id)
    mapping_path, mapping_payload = _eligible_mapping_payload(
        quest_root=quest_root,
        study_root=study_root,
    )
    anchor_repairable = bool(mapping_payload)
    if not any((repairable_surface, stale_delivery, anchor_repairable, bundle_stage_repair)):
        return None
    if (
        (repairable_surface or anchor_repairable)
        and bounded_analysis_action is None
        and not prefer_startup_freshness_work_unit
    ):
        return None

    latest_batch = _latest_batch_record(study_root=study_root)
    current_eval_id = str(publication_eval_payload.get("eval_id") or "").strip()
    if _latest_batch_closed_for_eval(latest_batch, current_eval_id):
        return None

    if prefer_startup_freshness_work_unit and bundle_stage_repair:
        selected_action = gate_clearing_batch_submission.bundle_stage_batch_action(
            source_action=same_line_action or controller_return_action,
            gate_report=gate_report,
        )
    elif anchor_repairable or repairable_surface:
        selected_action = dict(bounded_analysis_action or {})
    elif bundle_stage_repair:
        selected_action = gate_clearing_batch_submission.bundle_stage_batch_action(
            source_action=same_line_action or controller_return_action,
            gate_report=gate_report,
        )
    else:
        return None

    reason_bits: list[str] = []
    if anchor_repairable:
        reason_bits.append("scientific-anchor fields can be frozen from the latest bounded analysis output")
    if repairable_surface:
        reason_bits.append("paper-facing display/reporting blockers are deterministic repair candidates")
    if stale_delivery:
        reason_bits.append("study delivery mirror is stale but repairable through controller-owned replay")
    if bundle_stage_repair:
        reason_bits.append("finalize/submission bundle blockers are deterministic same-line repair candidates")
    return {
        **selected_action,
        "controller_action_type": "run_gate_clearing_batch",
        "reason": (
            str(selected_action.get("reason") or "").strip()
            or "Run one controller-owned gate-clearing batch before sending the study back into the next managed route."
        ),
        "gate_clearing_batch_reason": "; ".join(reason_bits),
        "gate_clearing_batch_mapping_path": str(mapping_path) if mapping_path is not None else None,
        "work_unit_fingerprint": publication_work_unit_payload.get("fingerprint"),
        "gate_fingerprint": gate_report.get("gate_fingerprint"),
        "evaluated_source_signature": gate_report.get("submission_minimal_evaluated_source_signature"),
        "authority_source_signature": gate_report.get("submission_minimal_authority_source_signature"),
        "blocking_artifact_refs": gate_report.get("blocking_artifact_refs") or [],
        "blocking_work_units": publication_work_unit_payload.get("blocking_work_units") or [],
        "next_work_unit": publication_work_unit_payload.get("next_work_unit"),
    }


def _freeze_scientific_anchor_fields(
    *,
    study_root: Path,
    study_id: str,
    profile: WorkspaceProfile,
    mapping_path: Path,
) -> dict[str, Any]:
    return scientific_anchor.freeze_scientific_anchor_fields(
        study_root=study_root,
        study_id=study_id,
        profile=profile,
        mapping_path=mapping_path,
        study_runtime_router_controller=study_runtime_router,
    )


def _repair_paper_live_paths(
    *,
    profile: WorkspaceProfile,
    quest_id: str,
    workspace_root: Path,
    current_workspace_root: Path,
) -> dict[str, Any]:
    return execution_helpers.repair_paper_live_paths(
        profile=profile,
        quest_id=quest_id,
        workspace_root=workspace_root,
        current_workspace_root=current_workspace_root,
    )


def _materialize_display_surface(*, paper_root: Path) -> dict[str, Any]:
    return display_surface_materialization.materialize_display_surface(paper_root=paper_root)


def _publication_shell_surface_needs_sync(*, study_root: Path, paper_root: Path) -> bool:
    return display_refresh.publication_shell_surface_needs_sync(study_root=study_root, paper_root=paper_root)


def _legacy_time_to_event_grouped_payload_normalization_candidates(
    *,
    paper_root: Path,
) -> tuple[Path, list[str], str | None, str | None]:
    return display_refresh.legacy_time_to_event_grouped_payload_normalization_candidates(
        paper_root=paper_root,
        display_surface_materialization_controller=display_surface_materialization,
    )


def _normalize_legacy_time_to_event_grouped_payloads(*, paper_root: Path) -> dict[str, Any]:
    return display_refresh.normalize_legacy_time_to_event_grouped_payloads(
        paper_root=paper_root,
        display_surface_materialization_controller=display_surface_materialization,
    )


def _legacy_time_to_event_grouped_payloads_need_normalization(*, paper_root: Path) -> bool:
    return display_refresh.legacy_time_to_event_grouped_payloads_need_normalization(
        paper_root=paper_root,
        display_surface_materialization_controller=display_surface_materialization,
    )


def _time_to_event_risk_group_surface_present(*, paper_root: Path) -> bool:
    return display_refresh.time_to_event_risk_group_surface_present(paper_root=paper_root)


def _time_to_event_direct_migration_display_inputs_need_refresh(*, paper_root: Path) -> bool:
    return display_refresh.time_to_event_direct_migration_display_inputs_need_refresh(
        paper_root=paper_root,
        display_surface_materialization_controller=display_surface_materialization,
    )


def _legacy_direct_migration_feature_shift_payload_present(
    *,
    paper_root: Path,
    input_schema_id: str,
    display_id: str,
) -> bool:
    return display_refresh.legacy_direct_migration_feature_shift_payload_present(
        paper_root=paper_root,
        input_schema_id=input_schema_id,
        display_id=display_id,
    )


def _run_workspace_display_repair_script(*, paper_root: Path) -> dict[str, Any]:
    return execution_helpers.run_workspace_display_repair_script(paper_root=paper_root)


def _create_submission_minimal_package(**kwargs: Any) -> dict[str, Any]:
    return create_submission_minimal_package_with_route(submission_minimal=submission_minimal, **kwargs)

def _sync_submission_minimal_delivery(**kwargs: Any) -> dict[str, Any]:
    return sync_submission_minimal_delivery_with_route(study_delivery_sync=study_delivery_sync, **kwargs)


def run_gate_clearing_batch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    quest_id: str,
    source: str = "med_autoscience",
    control_plane_route_context: dict[str, Any] | None = None,
    route_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_route_context = control_plane_route_context or route_context
    resolved_study_root = Path(study_root).expanduser().resolve()
    quest_root = _quest_root(profile, quest_id=quest_id)
    gate_state = publication_gate.build_gate_state(quest_root)
    gate_report = publication_gate.build_gate_report(gate_state)
    publication_eval_payload = read_publication_eval_latest(study_root=resolved_study_root)
    latest_batch = _latest_batch_record(study_root=resolved_study_root)
    current_eval_id = str(publication_eval_payload.get("eval_id") or "").strip()
    controller_decision_work_unit = gate_clearing_batch_currentness.controller_decision_publication_work_unit(
        study_root=resolved_study_root,
        study_id=study_id,
        quest_id=quest_id,
        source_eval_id=current_eval_id,
    )
    if _latest_batch_closed_for_eval(latest_batch, current_eval_id):
        return {
            "ok": True,
            "status": "skipped_duplicate_eval",
            "source_eval_id": current_eval_id,
            "latest_record_path": str(stable_gate_clearing_batch_path(study_root=resolved_study_root)),
        }

    paper_root = gate_state.paper_root
    if paper_root is None:
        return {
            "ok": False,
            "status": "blocked_no_paper_root",
            "source_eval_id": current_eval_id,
        }

    current_workspace_root = _current_workspace_root(
        quest_root=quest_root,
        default=paper_root.parent,
    )
    mapping_path, mapping_payload = _eligible_mapping_payload(
        quest_root=quest_root,
        study_root=resolved_study_root,
    )
    gate_blockers = _gate_blockers(gate_report)
    bundle_stage_repair = gate_clearing_batch_submission.bundle_stage_repair_requested(gate_report=gate_report)
    study_delivery_status = gate_clearing_batch_submission.study_delivery_status(gate_report)
    submission_minimal_refresh_requested = gate_clearing_batch_submission.submission_minimal_refresh_requested(
        gate_report=gate_report
    )
    direct_submission_delivery_sync_requested = (
        bundle_stage_repair
        and not submission_minimal_refresh_requested
        and gate_clearing_batch_submission.direct_submission_delivery_sync_requested(gate_report=gate_report)
        and study_delivery_sync.can_sync_study_delivery(paper_root=paper_root)
    )
    authority_settle_delivery_redrive_requested = (
        gate_clearing_batch_authority_redrive.previous_delivery_sync_awaited_authority_settle(latest_batch)
        and study_delivery_status.startswith("stale")
        and study_delivery_sync.can_sync_study_delivery(paper_root=paper_root)
    )
    if authority_settle_delivery_redrive_requested:
        direct_submission_delivery_sync_requested = True
        submission_minimal_refresh_requested = False

    work_unit_selection = gate_clearing_batch_currentness.publication_work_unit_selection(
        publication_eval_payload=publication_eval_payload,
        latest_batch=latest_batch,
        gate_report=gate_report,
        authority_settle_delivery_redrive_requested=authority_settle_delivery_redrive_requested,
        direct_submission_delivery_sync_requested=direct_submission_delivery_sync_requested,
        controller_decision_work_unit=controller_decision_work_unit,
    )
    explicit_next_work_unit = work_unit_selection["explicit_next_work_unit"]
    current_publication_work_unit_payload = work_unit_selection["current_publication_work_unit_payload"]
    selected_publication_work_unit = work_unit_selection["selected_publication_work_unit"]
    work_unit_currentness = work_unit_selection["work_unit_currentness"]
    terminal_reason = work_unit_selection["terminal_reason"]
    selected_work_unit_id = _non_empty_text(
        selected_publication_work_unit.get("unit_id") if isinstance(selected_publication_work_unit, dict) else None
    )
    controller_decision_work_unit_id = _non_empty_text(
        controller_decision_work_unit.get("unit_id") if isinstance(controller_decision_work_unit, dict) else None
    )
    if terminal_reason is not None:
        return gate_clearing_batch_currentness.write_gate_specificity_terminal_batch(
            record_path=stable_gate_clearing_batch_path(study_root=resolved_study_root),
            lifecycle_path=publication_work_unit_lifecycle.stable_publication_work_unit_lifecycle_path(
                study_root=resolved_study_root
            ),
            schema_version=SCHEMA_VERSION,
            study_root=resolved_study_root,
            study_id=study_id,
            quest_id=quest_id,
            paper_root=paper_root,
            current_workspace_root=current_workspace_root,
            source_eval_id=current_eval_id,
            gate_report=gate_report,
            gate_blockers=_gate_blockers(gate_report),
            explicit_publication_work_unit=explicit_next_work_unit,
            terminal_publication_work_unit=gate_clearing_batch_currentness.terminal_publication_work_unit(
                work_unit_selection
            ),
            current_publication_work_unit_payload=current_publication_work_unit_payload,
            work_unit_currentness=work_unit_currentness,
            terminal_reason=terminal_reason,
            gate_replay_timing=publication_work_unit_lifecycle.instant_timing(clock=_clock_snapshot),
        )

    if (
        isinstance(selected_publication_work_unit, dict)
        and _non_empty_text(selected_publication_work_unit.get("unit_id"))
        in {"publication_gate_replay", "submission_delivery_sync_closure"}
        and gate_clearing_batch_replay_closure.stale_gate_replay_closed(latest_batch, gate_report=gate_report)
    ):
        return gate_clearing_batch_currentness.stale_gate_replay_closed_result(
            source_eval_id=current_eval_id,
            latest_record_path=stable_gate_clearing_batch_path(study_root=resolved_study_root),
            latest_batch=latest_batch,
            gate_report=gate_report,
            selected_publication_work_unit=selected_publication_work_unit,
            current_publication_work_unit_payload=current_publication_work_unit_payload,
            work_unit_currentness=work_unit_currentness,
        )

    repair_units: list[GateClearingRepairUnit] = []
    if mapping_payload:
        repair_units.append(
            GateClearingRepairUnit(
                unit_id="freeze_scientific_anchor_fields",
                label="Freeze scientific-anchor fields from the latest bounded-analysis output",
                parallel_safe=True,
                run=lambda: _freeze_scientific_anchor_fields(
                    study_root=resolved_study_root,
                    study_id=study_id,
                    profile=profile,
                    mapping_path=mapping_path,
                ),
            )
        )
    gate_blockers = {
        str(item or "").strip()
        for item in (gate_report.get("blockers") or [])
        if str(item or "").strip()
    }
    display_repair_script_path = paper_root / "build" / "generate_display_exports.py"
    if (
        not authority_settle_delivery_redrive_requested
        and medical_surface_display_repair_requested(
            gate_report,
            submission_minimal_repair_gate_blockers=gate_clearing_batch_submission.SUBMISSION_MINIMAL_REPAIR_GATE_BLOCKERS,
        )
    ):
        repair_units.append(
            GateClearingRepairUnit(
                unit_id="repair_paper_live_paths",
                label="Repair runtime-owned paper live paths before publication-surface replay",
                parallel_safe=True,
                run=lambda: _repair_paper_live_paths(
                    profile=profile,
                    quest_id=quest_id,
                    workspace_root=paper_root.parent,
                    current_workspace_root=current_workspace_root,
                ),
            )
        )
        if display_repair_script_path.exists():
            repair_units.append(
                GateClearingRepairUnit(
                    unit_id="workspace_display_repair_script",
                    label="Run the workspace-authored display repair script before gate replay",
                    parallel_safe=True,
                    depends_on=_existing_dependency_ids(repair_units, "repair_paper_live_paths"),
                    run=lambda: _run_workspace_display_repair_script(paper_root=paper_root),
                )
            )
        else:
            if gate_clearing_batch_transportability.transportability_reporting_surface_needs_sync(
                study_root=resolved_study_root,
                paper_root=paper_root,
                profile=profile,
            ):
                repair_units.append(
                    GateClearingRepairUnit(
                        unit_id="sync_transportability_reporting_surface",
                        label="Sync transportability reporting display contract before surface materialization",
                        parallel_safe=True,
                        depends_on=_existing_dependency_ids(repair_units, "repair_paper_live_paths"),
                        run=lambda: gate_clearing_batch_transportability.sync_transportability_reporting_surface(
                            study_root=resolved_study_root,
                            paper_root=paper_root,
                            profile=profile,
                        ),
                    )
                )
            if _time_to_event_direct_migration_display_inputs_need_refresh(paper_root=paper_root):
                repair_units.append(
                    GateClearingRepairUnit(
                        unit_id="time_to_event_direct_migration",
                        label="Refresh canonical time-to-event direct-migration display inputs before surface materialization",
                        parallel_safe=True,
                        depends_on=_existing_dependency_ids(repair_units, "repair_paper_live_paths"),
                        run=lambda: time_to_event_direct_migration.run_time_to_event_direct_migration(
                            study_root=resolved_study_root,
                            paper_root=paper_root,
                        ),
                    )
                )
            if (
                _legacy_time_to_event_grouped_payloads_need_normalization(paper_root=paper_root)
                or (
                    _time_to_event_risk_group_surface_present(paper_root=paper_root)
                    and any(
                        unit.unit_id == "sync_transportability_reporting_surface"
                        for unit in repair_units
                    )
                )
            ):
                repair_units.append(
                    GateClearingRepairUnit(
                        unit_id="normalize_legacy_time_to_event_grouped_payloads",
                        label=(
                            "Normalize legacy time-to-event grouped display payload templates "
                            "before surface materialization"
                        ),
                        parallel_safe=True,
                        depends_on=_existing_dependency_ids(
                            repair_units,
                            "repair_paper_live_paths",
                            "sync_transportability_reporting_surface",
                            "time_to_event_direct_migration",
                        ),
                        run=lambda: _normalize_legacy_time_to_event_grouped_payloads(paper_root=paper_root),
                    )
                )
            if _publication_shell_surface_needs_sync(
                study_root=resolved_study_root,
                paper_root=paper_root,
            ):
                repair_units.append(
                    GateClearingRepairUnit(
                        unit_id="sync_publication_shell_surface",
                        label="Sync publication shell table inputs before surface materialization",
                        parallel_safe=True,
                        depends_on=_existing_dependency_ids(
                            repair_units,
                            "repair_paper_live_paths",
                        ),
                        run=lambda: publication_shell_sync.run_publication_shell_sync(
                            study_root=resolved_study_root,
                            paper_root=paper_root,
                        ),
                    )
                )
            repair_units.append(
                GateClearingRepairUnit(
                    unit_id="materialize_display_surface",
                    label="Refresh display catalogs and generated paper-facing exports",
                    parallel_safe=True,
                    depends_on=_existing_dependency_ids(
                        repair_units,
                        "repair_paper_live_paths",
                        "sync_transportability_reporting_surface",
                        "time_to_event_direct_migration",
                        "normalize_legacy_time_to_event_grouped_payloads",
                        "sync_publication_shell_surface",
                    ),
                    run=lambda: _materialize_display_surface(paper_root=paper_root),
                )
            )
    elif not authority_settle_delivery_redrive_requested and bundle_stage_repair and display_repair_script_path.exists():
        repair_units.append(
            GateClearingRepairUnit(
                unit_id="workspace_display_repair_script",
                label="Run the workspace-authored display repair script before bundle-stage gate replay",
                parallel_safe=True,
                run=lambda: _run_workspace_display_repair_script(paper_root=paper_root),
            )
        )
    if direct_submission_delivery_sync_requested:
        repair_units.append(
            GateClearingRepairUnit(
                unit_id="sync_submission_minimal_delivery",
                label="Refresh the study-owned submission-minimal delivery mirror before gate replay",
                parallel_safe=True,
                depends_on=_existing_dependency_ids(
                    repair_units,
                    "repair_paper_live_paths",
                    "workspace_display_repair_script",
                    "materialize_display_surface",
                ),
                run=lambda: gate_clearing_batch_submission.sync_submission_minimal_delivery_after_settle(
                    paper_root=paper_root,
                    profile=profile,
                    sync_submission_minimal_delivery=_route_bound(
                        function=_sync_submission_minimal_delivery,
                        control_plane_route_context=resolved_route_context,
                    ),
                    path_fingerprints=_path_fingerprints,
                    settle_window_ns=CURRENT_PACKAGE_AUTHORITY_SETTLE_WINDOW_NS,
                ),
            )
        )
    if bundle_stage_repair and submission_minimal_refresh_requested:
        submission_refresh_dependencies = (
            ()
            if (
                selected_work_unit_id == "submission_minimal_refresh"
                and controller_decision_work_unit_id == "submission_minimal_refresh"
            )
            else _existing_dependency_ids(
                repair_units,
                "repair_paper_live_paths",
                "workspace_display_repair_script",
                "materialize_display_surface",
            )
        )
        repair_units.append(
            GateClearingRepairUnit(
                unit_id="create_submission_minimal_package",
                label="Regenerate submission-minimal assets before gate replay",
                parallel_safe=False,
                depends_on=submission_refresh_dependencies,
                run=lambda: _route_call(_create_submission_minimal_package, paper_root=paper_root, profile=profile, control_plane_route_context=resolved_route_context),
            )
        )
    repair_units = filter_repair_units_for_publication_work_unit(
        repair_units,
        next_work_unit=selected_publication_work_unit,
        additional_allowed_unit_ids=gate_clearing_batch_authority_redrive.analysis_work_unit_authority_closure_unit_ids(
            selected_publication_work_unit=explicit_next_work_unit,
            submission_minimal_refresh_requested=submission_minimal_refresh_requested,
            repair_units=repair_units,
        ),
    )
    repair_unit_execution_plan = gate_clearing_batch_scheduler.build_repair_unit_execution_plan(repair_units)
    if not repair_units and study_delivery_status.startswith("stale"):
        # Let publication_gate.run_controller(apply=True) own stale delivery refresh even when
        # there are no other deterministic repairs to launch in parallel.
        repair_units = []

    if not repair_units and not bundle_stage_repair and not study_delivery_status.startswith("stale"):
        return {
            "ok": False,
            "status": "no_repair_units",
            "source_eval_id": current_eval_id,
            "gate_blockers": sorted(gate_blockers),
        }
    unit_results, unit_fingerprints, execution_summary = _execute_repair_units(
        repair_units=repair_units,
        latest_batch=latest_batch,
        paper_root=paper_root,
        gate_report=gate_report,
        profile=profile,
    )
    submission_delivery.append_delivery_sync_after_submission_refresh(
        unit_results=unit_results,
        execution_summary=execution_summary,
        study_delivery_status=study_delivery_status,
        paper_root=paper_root,
        profile=profile,
        sync_submission_minimal_delivery=_route_bound(
            function=_sync_submission_minimal_delivery,
            control_plane_route_context=resolved_route_context,
        ),
        path_fingerprints=_path_fingerprints,
        settle_window_ns=CURRENT_PACKAGE_AUTHORITY_SETTLE_WINDOW_NS,
        clock_snapshot=_clock_snapshot,
    )

    gate_replay, gate_replay_timing = publication_work_unit_lifecycle.timed_step(
        clock=_clock_snapshot,
        run=lambda: publication_gate.run_controller(
            quest_root=quest_root,
            apply=True,
            source=source,
            enqueue_intervention=False,
            control_plane_route_context=resolved_route_context,
        ),
    )
    gate_replay_step = publication_work_unit_lifecycle.gate_replay_step(
        gate_replay=gate_replay,
        timing=gate_replay_timing,
    )
    lifecycle_record = publication_work_unit_lifecycle.build_lifecycle_record(
        source_eval_id=current_eval_id,
        study_id=study_id,
        quest_id=quest_id,
        selected_work_unit=selected_publication_work_unit,
        unit_results=unit_results,
        gate_replay=gate_replay,
    )
    selected_publication_work_unit = publication_work_unit_lifecycle.enrich_selected_work_unit(
        selected_work_unit=selected_publication_work_unit,
        lifecycle_record=lifecycle_record,
    )
    current_package_freshness_proof = gate_clearing_batch_package_freshness.write_current_package_freshness_proof(
        study_root=resolved_study_root,
        source_eval_id=current_eval_id,
        gate_report=gate_report,
        unit_results=unit_results,
        clock=_clock_snapshot,
        schema_version=SCHEMA_VERSION,
    )
    stale_gate_replay_closure = gate_clearing_batch_replay_closure.stale_gate_replay_closure_marker(
        gate_report=gate_report,
        gate_replay=gate_replay,
        gate_replay_timing=gate_replay_timing,
        unit_results=unit_results,
        schema_version=SCHEMA_VERSION,
    )
    selected_publication_work_unit, closure_lifecycle_record = (
        gate_clearing_batch_currentness.selected_work_unit_after_stale_delivery_closure(
            stale_gate_replay_closure=stale_gate_replay_closure,
            selected_publication_work_unit=selected_publication_work_unit,
            source_eval_id=current_eval_id,
            study_id=study_id,
            quest_id=quest_id,
            unit_results=unit_results,
            gate_replay=gate_replay,
        )
    )
    lifecycle_record = closure_lifecycle_record or lifecycle_record
    record = gate_clearing_batch_currentness.build_executed_batch_record(
        schema_version=SCHEMA_VERSION,
        study_root=resolved_study_root,
        source_eval_id=current_eval_id,
        quest_id=quest_id,
        study_id=study_id,
        paper_root=paper_root,
        current_workspace_root=current_workspace_root,
        gate_blockers=gate_blockers,
        gate_report=gate_report,
        selected_publication_work_unit=selected_publication_work_unit,
        explicit_publication_work_unit=explicit_next_work_unit,
        current_publication_work_unit_payload=current_publication_work_unit_payload,
        work_unit_currentness=work_unit_currentness,
        unit_results=unit_results,
        unit_fingerprints=unit_fingerprints,
        repair_unit_execution_plan=repair_unit_execution_plan,
        execution_summary=execution_summary,
        gate_replay=gate_replay,
        gate_replay_step=gate_replay_step,
        lifecycle_record=lifecycle_record,
        repair_blocking_artifact_refs=_unit_blocking_artifact_refs(unit_results),
        current_package_freshness_proof=current_package_freshness_proof,
        stale_gate_replay_closure=stale_gate_replay_closure,
    )
    record_path = stable_gate_clearing_batch_path(study_root=resolved_study_root)
    _write_json(record_path, record)
    _write_json(
        publication_work_unit_lifecycle.stable_publication_work_unit_lifecycle_path(
            study_root=resolved_study_root
        ),
        lifecycle_record,
    )
    return {
        "ok": True,
        "status": "executed",
        "record_path": str(record_path),
        **record,
    }
