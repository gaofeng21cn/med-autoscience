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
from med_autoscience.controllers.gate_clearing_batch_parts import batch_context
from med_autoscience.controllers.gate_clearing_batch_parts import execution_helpers
from med_autoscience.controllers.gate_clearing_batch_parts import io_utils
from med_autoscience.controllers.gate_clearing_batch_parts import path_selection
from med_autoscience.controllers.gate_clearing_batch_parts import repair_plan
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


_latest_unit_result = gate_clearing_batch_execution.latest_unit_result
_latest_unit_status = gate_clearing_batch_execution.latest_unit_status
_unit_status_is_success = gate_clearing_batch_execution.unit_status_is_success
_latest_unit_success_status = gate_clearing_batch_execution.latest_unit_success_status
_latest_unit_fingerprint = gate_clearing_batch_execution.latest_unit_fingerprint
_can_skip_repair_unit = gate_clearing_batch_execution.can_skip_repair_unit
_unit_status_blocks_dependents = gate_clearing_batch_execution.unit_status_blocks_dependents
_existing_dependency_ids = gate_clearing_batch_execution.existing_dependency_ids


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


_reuse_embedded_submission_delivery_sync = gate_clearing_batch_execution.reuse_embedded_submission_delivery_sync


def _latest_batch_record(*, study_root: Path) -> dict[str, Any]:
    return _read_json(stable_gate_clearing_batch_path(study_root=study_root))


def _gate_replay_report_payload(gate_replay: dict[str, Any]) -> dict[str, Any]:
    report_path_text = _non_empty_text(gate_replay.get("report_json")) or _non_empty_text(
        gate_replay.get("latest_gate_path")
    )
    if report_path_text is None:
        return gate_replay
    report_payload = _read_json(Path(report_path_text).expanduser())
    if not report_payload:
        return gate_replay
    return {**gate_replay, **report_payload}


def _freshness_gate_report_payload(*, gate_report: dict[str, Any], gate_replay: dict[str, Any]) -> dict[str, Any]:
    replay_report = _gate_replay_report_payload(gate_replay)
    if gate_clearing_batch_submission.study_delivery_status(replay_report) == "current":
        return replay_report
    return gate_report


def _closed_batch_current_freshness_proof(
    *,
    latest_batch: dict[str, Any],
    study_root: Path,
    source_eval_id: str,
) -> dict[str, Any] | None:
    if isinstance(latest_batch.get("current_package_freshness_proof"), dict):
        return dict(latest_batch["current_package_freshness_proof"])
    gate_replay = latest_batch.get("gate_replay")
    if not isinstance(gate_replay, dict):
        return None
    return gate_clearing_batch_package_freshness.write_current_package_freshness_proof(
        study_root=study_root,
        source_eval_id=source_eval_id,
        gate_report=_gate_replay_report_payload(gate_replay),
        unit_results=[],
        clock=_clock_snapshot,
        schema_version=SCHEMA_VERSION,
    )


def _base_publication_work_unit(value: object) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    return {
        key: item
        for key, item in value.items()
        if key not in {"lifecycle", "lifecycle_status", "retry", "status"}
    }


def _closed_batch_lifecycle_record(
    *,
    latest_batch: dict[str, Any],
    study_id: str,
    quest_id: str,
    source_eval_id: str,
    gate_report: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    selected_work_unit = _base_publication_work_unit(latest_batch.get("selected_publication_work_unit"))
    if selected_work_unit is None:
        existing_lifecycle = latest_batch.get("publication_work_unit_lifecycle")
        if isinstance(existing_lifecycle, dict):
            selected_work_unit = _base_publication_work_unit(existing_lifecycle.get("work_unit"))
    unit_results = [
        dict(item)
        for item in (latest_batch.get("unit_results") or [])
        if isinstance(item, dict)
    ]
    gate_replay = dict(latest_batch.get("gate_replay") or {})
    if _current_gate_settles_authority_sync(latest_batch=latest_batch, gate_report=gate_report):
        unit_results = [
            {
                **item,
                "status": "settled_by_current_gate"
                if _non_empty_text(item.get("status")) == "skipped_authority_not_settled"
                else item.get("status"),
            }
            for item in unit_results
        ]
        gate_replay = {
            **gate_replay,
            "status": "clear",
            "allow_write": True,
        }
    if selected_work_unit is None or not unit_results:
        return None
    return publication_work_unit_lifecycle.build_lifecycle_record(
        source_eval_id=source_eval_id,
        study_id=study_id,
        quest_id=quest_id,
        selected_work_unit=selected_work_unit,
        unit_results=unit_results,
        gate_replay=gate_replay,
    )


def _normalize_closed_batch_lifecycle_surface(
    *,
    latest_batch: dict[str, Any],
    study_root: Path,
    study_id: str,
    quest_id: str,
    source_eval_id: str,
    gate_report: dict[str, Any] | None = None,
) -> tuple[dict[str, Any] | None, bool]:
    lifecycle_record = _closed_batch_lifecycle_record(
        latest_batch=latest_batch,
        study_id=study_id,
        quest_id=quest_id,
        source_eval_id=source_eval_id,
        gate_report=gate_report,
    )
    if lifecycle_record is None:
        return None, False
    lifecycle_path = publication_work_unit_lifecycle.stable_publication_work_unit_lifecycle_path(
        study_root=study_root
    )
    current_record = _read_json(lifecycle_path)
    current_status = _non_empty_text(current_record.get("status"))
    current_source_eval_id = _non_empty_text(current_record.get("source_eval_id"))
    normalized_status = _non_empty_text(lifecycle_record.get("status"))
    if (
        current_source_eval_id == source_eval_id
        and current_status == normalized_status
        and ("retry" in current_record) == ("retry" in lifecycle_record)
    ):
        return dict(current_record), False
    _write_json(lifecycle_path, lifecycle_record)
    return lifecycle_record, True


def _latest_batch_closed_for_eval(latest_batch: dict[str, Any], current_eval_id: str | None) -> bool:
    return gate_clearing_batch_currentness.batch_closed_for_source_eval(latest_batch, source_eval_id=current_eval_id)


def _latest_batch_closed_for_current_gate(
    latest_batch: dict[str, Any],
    current_eval_id: str | None,
    gate_report: dict[str, Any],
) -> bool:
    return gate_clearing_batch_currentness.batch_closed_for_source_eval(
        latest_batch,
        source_eval_id=current_eval_id,
        gate_report=gate_report,
    )


def _current_gate_settles_authority_sync(
    *,
    latest_batch: dict[str, Any],
    gate_report: dict[str, Any] | None,
) -> bool:
    if not isinstance(gate_report, dict):
        return False
    return gate_clearing_batch_currentness.batch_closed_for_source_eval(
        latest_batch,
        source_eval_id=_non_empty_text(latest_batch.get("source_eval_id")),
        gate_report=gate_report,
    ) and not gate_clearing_batch_currentness.batch_closed_for_source_eval(
        latest_batch,
        source_eval_id=_non_empty_text(latest_batch.get("source_eval_id")),
    )


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


def _controller_route_context_for_selected_work_unit(
    *,
    selected_publication_work_unit: dict[str, Any] | None,
    gate_report: dict[str, Any],
    current_publication_work_unit_payload: dict[str, Any],
    source_eval_id: str | None,
) -> dict[str, Any] | None:
    if not isinstance(selected_publication_work_unit, dict):
        return None
    work_unit_id = _non_empty_text(selected_publication_work_unit.get("unit_id"))
    if work_unit_id is None:
        return None
    return {
        "controller_route_context": {
            "control_surface": "gate_clearing_batch",
            "controller_action_type": "run_gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "requires_human_confirmation": False,
            "source_eval_id": source_eval_id,
            "gate_fingerprint": _non_empty_text(gate_report.get("gate_fingerprint")),
            "work_unit_fingerprint": _non_empty_text(current_publication_work_unit_payload.get("fingerprint")),
        }
    }


def _merge_control_plane_route_contexts(*contexts: dict[str, Any] | None) -> dict[str, Any] | None:
    merged: dict[str, Any] = {}
    for context in contexts:
        if isinstance(context, dict):
            merged.update(context)
    return merged or None


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
    context = batch_context.build_gate_clearing_batch_context(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        quest_id=quest_id,
        control_plane_route_context=control_plane_route_context,
        route_context=route_context,
        quest_root_for_profile=_quest_root,
        publication_gate_controller=publication_gate,
        read_publication_eval_latest_fn=read_publication_eval_latest,
        latest_batch_record=_latest_batch_record,
        latest_batch_closed_for_eval=_latest_batch_closed_for_eval,
        current_workspace_root_fn=_current_workspace_root,
        eligible_mapping_payload=_eligible_mapping_payload,
        gate_blockers_fn=_gate_blockers,
        submission_controller=gate_clearing_batch_submission,
        authority_redrive_controller=gate_clearing_batch_authority_redrive,
        study_delivery_sync_controller=study_delivery_sync,
        currentness_controller=gate_clearing_batch_currentness,
    )
    resolved_route_context = context.resolved_route_context
    resolved_study_root = context.resolved_study_root
    quest_root = context.quest_root
    gate_report = context.gate_report
    publication_eval_payload = context.publication_eval_payload
    latest_batch = context.latest_batch
    current_eval_id = context.current_eval_id
    controller_decision_work_unit = context.controller_decision_work_unit
    if _latest_batch_closed_for_current_gate(latest_batch, current_eval_id, gate_report):
        lifecycle_record, lifecycle_normalized = _normalize_closed_batch_lifecycle_surface(
            latest_batch=latest_batch,
            study_root=resolved_study_root,
            study_id=study_id,
            quest_id=quest_id,
            source_eval_id=current_eval_id,
            gate_report=gate_report,
        )
        current_package_freshness_proof = _closed_batch_current_freshness_proof(
            latest_batch=latest_batch,
            study_root=resolved_study_root,
            source_eval_id=current_eval_id,
        )
        result = {
            "ok": True,
            "status": "skipped_duplicate_eval",
            "source_eval_id": current_eval_id,
            "latest_record_path": str(stable_gate_clearing_batch_path(study_root=resolved_study_root)),
            "current_package_freshness_proof": current_package_freshness_proof,
        }
        if lifecycle_record is not None:
            result["publication_work_unit_lifecycle"] = lifecycle_record
            result["publication_work_unit_lifecycle_normalized"] = lifecycle_normalized
        return result

    paper_root = context.paper_root
    if paper_root is None:
        return {
            "ok": False,
            "status": "blocked_no_paper_root",
            "source_eval_id": current_eval_id,
        }

    current_workspace_root = context.current_workspace_root
    if current_workspace_root is None:
        raise ValueError("gate-clearing batch context requires current_workspace_root when paper_root is available")
    mapping_payload = context.mapping_payload
    gate_blockers = context.gate_blockers
    bundle_stage_repair = context.bundle_stage_repair
    study_delivery_status = context.study_delivery_status
    submission_minimal_refresh_requested = context.submission_minimal_refresh_requested
    direct_submission_delivery_sync_requested = context.direct_submission_delivery_sync_requested
    authority_settle_delivery_redrive_requested = context.authority_settle_delivery_redrive_requested
    work_unit_selection = context.work_unit_selection
    if work_unit_selection is None:
        raise ValueError("gate-clearing batch context requires work_unit_selection when paper_root is available")
    explicit_next_work_unit = work_unit_selection["explicit_next_work_unit"]
    current_publication_work_unit_payload = work_unit_selection["current_publication_work_unit_payload"]
    selected_publication_work_unit = work_unit_selection["selected_publication_work_unit"]
    resolved_route_context = _merge_control_plane_route_contexts(
        resolved_route_context,
        _controller_route_context_for_selected_work_unit(
            selected_publication_work_unit=selected_publication_work_unit,
            gate_report=gate_report,
            current_publication_work_unit_payload=current_publication_work_unit_payload,
            source_eval_id=current_eval_id,
        ),
    )
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
        in {
            "publication_gate_replay",
            "submission_delivery_sync_closure",
            "submission_delivery_terminal_blocker",
        }
        and gate_clearing_batch_replay_closure.stale_gate_replay_closed(latest_batch, gate_report=gate_report)
    ):
        skipped_closed_result = gate_clearing_batch_currentness.stale_gate_replay_closed_result(
            source_eval_id=current_eval_id,
            latest_record_path=stable_gate_clearing_batch_path(study_root=resolved_study_root),
            latest_batch=latest_batch,
            gate_report=gate_report,
            selected_publication_work_unit=selected_publication_work_unit,
            current_publication_work_unit_payload=current_publication_work_unit_payload,
            work_unit_currentness=work_unit_currentness,
        )
        current_package_freshness_proof = _closed_batch_current_freshness_proof(
            latest_batch=latest_batch,
            study_root=resolved_study_root,
            source_eval_id=current_eval_id,
        )
        if current_package_freshness_proof is not None:
            skipped_closed_result["current_package_freshness_proof"] = current_package_freshness_proof
        return skipped_closed_result

    repair_units = repair_plan.build_gate_clearing_repair_units(
        repair_unit_cls=GateClearingRepairUnit,
        profile=profile,
        study_id=study_id,
        study_root=resolved_study_root,
        quest_id=quest_id,
        paper_root=paper_root,
        current_workspace_root=current_workspace_root,
        mapping_path=context.mapping_path,
        mapping_payload=mapping_payload,
        gate_report=gate_report,
        authority_settle_delivery_redrive_requested=authority_settle_delivery_redrive_requested,
        bundle_stage_repair=bundle_stage_repair,
        direct_submission_delivery_sync_requested=direct_submission_delivery_sync_requested,
        submission_minimal_refresh_requested=submission_minimal_refresh_requested,
        selected_work_unit_id=selected_work_unit_id,
        controller_decision_work_unit_id=controller_decision_work_unit_id,
        resolved_route_context=resolved_route_context,
        existing_dependency_ids=_existing_dependency_ids,
        freeze_scientific_anchor_fields=_freeze_scientific_anchor_fields,
        repair_paper_live_paths=_repair_paper_live_paths,
        run_workspace_display_repair_script=_run_workspace_display_repair_script,
        materialize_display_surface=_materialize_display_surface,
        publication_shell_surface_needs_sync=_publication_shell_surface_needs_sync,
        time_to_event_direct_migration_display_inputs_need_refresh=_time_to_event_direct_migration_display_inputs_need_refresh,
        legacy_time_to_event_grouped_payloads_need_normalization=_legacy_time_to_event_grouped_payloads_need_normalization,
        time_to_event_risk_group_surface_present=_time_to_event_risk_group_surface_present,
        normalize_legacy_time_to_event_grouped_payloads=_normalize_legacy_time_to_event_grouped_payloads,
        sync_submission_minimal_delivery=_sync_submission_minimal_delivery,
        create_submission_minimal_package=_create_submission_minimal_package,
        route_bound=_route_bound,
        route_call=_route_call,
        path_fingerprints=_path_fingerprints,
        medical_surface_display_repair_requested=medical_surface_display_repair_requested,
        gate_clearing_batch_submission=gate_clearing_batch_submission,
        gate_clearing_batch_transportability=gate_clearing_batch_transportability,
        publication_shell_sync=publication_shell_sync,
        time_to_event_direct_migration=time_to_event_direct_migration,
        current_package_authority_settle_window_ns=CURRENT_PACKAGE_AUTHORITY_SETTLE_WINDOW_NS,
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
        selected_work_unit_id=selected_work_unit_id,
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
        gate_report=_freshness_gate_report_payload(gate_report=gate_report, gate_replay=gate_replay),
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
