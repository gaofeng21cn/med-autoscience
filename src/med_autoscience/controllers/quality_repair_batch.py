from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import gate_clearing_batch
from med_autoscience.controllers import gate_clearing_batch_blockers
from med_autoscience.controllers import gate_clearing_batch_currentness
from med_autoscience.controllers import publication_work_units
from med_autoscience.controllers import study_runtime_router
from med_autoscience.controllers.gate_clearing_batch_work_units import UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS
from med_autoscience.controllers.control_plane_route_gate import assert_control_plane_route_authorized
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.publication_eval_latest import read_publication_eval_latest
from med_autoscience.study_decision_record import StudyDecisionActionType, StudyDecisionType


SCHEMA_VERSION = 1
STABLE_QUALITY_REPAIR_BATCH_RELATIVE_PATH = Path("artifacts/controller/quality_repair_batch/latest.json")
EVAL_HYGIENE_QUALITY_SUMMARY_RELATIVE_PATH = Path("artifacts/eval_hygiene/evaluation_summary/latest.json")
LEGACY_QUALITY_SUMMARY_RELATIVE_PATH = Path("artifacts/evaluation_summary/latest.json")
_QUALITY_REPAIR_CLOSURE_STATES = frozenset({"quality_repair_required"})
_QUALITY_REPAIR_LANES = frozenset({"general_quality_repair", "quality_floor_blocker"})
_CANONICAL_PAPER_OWNER_REQUIRED_SURFACES = (
    Path("paper_bundle_manifest.json"),
    Path("draft.md"),
    Path("medical_manuscript_blueprint.json"),
    Path("medical_prose_review.json"),
    Path("claim_evidence_map.json"),
    Path("display_registry.json"),
    Path("results_narrative_map.json"),
    Path("figure_semantics_manifest.json"),
    Path("figures/figure_catalog.json"),
    Path("tables/table_catalog.json"),
)
_CANONICAL_PAPER_OWNER_PROJECTION_INPUT_SURFACES = tuple(
    relpath for relpath in _CANONICAL_PAPER_OWNER_REQUIRED_SURFACES if relpath != Path("display_registry.json")
)
_HYDRATION_PAPER_OWNER_INPUT_SURFACES = (
    Path("medical_analysis_contract.json"),
    Path("medical_reporting_contract.json"),
    Path("display_registry.json"),
    Path("reference_coverage_report.json"),
    Path("references.bib"),
)
_HYDRATION_PAPER_OWNER_INPUT_GLOBS = (
    "figures/*.shell.json",
    "tables/*.shell.json",
)


def stable_quality_repair_batch_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / STABLE_QUALITY_REPAIR_BATCH_RELATIVE_PATH


def _read_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _quality_summary_path(*, study_root: Path) -> Path:
    resolved_study_root = Path(study_root).expanduser().resolve()
    canonical_path = resolved_study_root / EVAL_HYGIENE_QUALITY_SUMMARY_RELATIVE_PATH
    if canonical_path.exists():
        return canonical_path
    return resolved_study_root / LEGACY_QUALITY_SUMMARY_RELATIVE_PATH


def _read_quality_summary(*, study_root: Path) -> dict[str, Any]:
    return _read_json_object(_quality_summary_path(study_root=study_root))


def _quality_repair_context(summary_payload: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    quality_closure_truth = (
        dict(summary_payload.get("quality_closure_truth") or {})
        if isinstance(summary_payload.get("quality_closure_truth"), Mapping)
        else {}
    )
    quality_execution_lane = (
        dict(summary_payload.get("quality_execution_lane") or {})
        if isinstance(summary_payload.get("quality_execution_lane"), Mapping)
        else {}
    )
    return quality_closure_truth, quality_execution_lane


def _quality_repair_required(summary_payload: Mapping[str, Any]) -> bool:
    quality_closure_truth, quality_execution_lane = _quality_repair_context(summary_payload)
    closure_state = _non_empty_text(quality_closure_truth.get("state"))
    lane_id = _non_empty_text(quality_execution_lane.get("lane_id"))
    return closure_state in _QUALITY_REPAIR_CLOSURE_STATES or lane_id in _QUALITY_REPAIR_LANES


def _gate_blockers(gate_report: Mapping[str, Any]) -> set[str]:
    return {
        text
        for item in (gate_report.get("blockers") or [])
        if (text := _non_empty_text(item)) is not None
    }


def _repairable_medical_surface(gate_report: Mapping[str, Any]) -> bool:
    return gate_clearing_batch_blockers.repairable_medical_surface(dict(gate_report))


def _repair_candidates(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    quest_id: str,
    gate_report: Mapping[str, Any],
    include_downstream_delivery: bool = True,
) -> list[str]:
    candidates: list[str] = []
    quest_root = profile.managed_runtime_quests_root / quest_id
    _, mapping_payload = gate_clearing_batch._eligible_mapping_payload(
        quest_root=quest_root,
        study_root=study_root,
    )
    if mapping_payload:
        candidates.append("scientific-anchor fields can be frozen from bounded-analysis output")
    if _repairable_medical_surface(gate_report):
        candidates.append("paper-facing display/reporting blockers are deterministic repair candidates")
    if include_downstream_delivery and "stale_study_delivery_mirror" in _gate_blockers(gate_report):
        candidates.append("study delivery mirror is stale but repairable through controller-owned replay")
    return candidates


def _latest_batch_record(*, study_root: Path) -> dict[str, Any]:
    return _read_json_object(stable_quality_repair_batch_path(study_root=study_root))


def _runtime_control_plane_route_context(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
) -> dict[str, Any] | None:
    status_payload = study_runtime_router.study_runtime_status(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        entry_mode=None,
        sync_runtime_summary=False,
        include_progress_projection=False,
    )
    if not isinstance(status_payload, Mapping):
        return None
    control_plane_snapshot = status_payload.get("control_plane_snapshot")
    if not isinstance(control_plane_snapshot, Mapping):
        return None
    return {"control_plane_snapshot": dict(control_plane_snapshot)}


def _controller_route_context_for_gate(
    *,
    gate_report: Mapping[str, Any],
    source_eval_id: str | None,
) -> dict[str, Any] | None:
    blockers = _gate_blockers(gate_report)
    if _non_empty_text(gate_report.get("current_required_action")) not in {
        "complete_bundle_stage",
        "continue_bundle_stage",
    }:
        return None
    if gate_clearing_batch.gate_clearing_batch_submission.submission_minimal_refresh_requested(
        gate_report=dict(gate_report)
    ):
        work_unit_id = "submission_minimal_refresh"
    elif "stale_study_delivery_mirror" in blockers:
        work_unit_id = "submission_delivery_sync_closure"
    else:
        return None
    return {
        "controller_route_context": {
            "control_surface": "quality_repair_batch",
            "controller_action_type": StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value,
            "work_unit_id": work_unit_id,
            "requires_human_confirmation": False,
            "source_eval_id": source_eval_id,
            "gate_fingerprint": _non_empty_text(gate_report.get("gate_fingerprint")),
            "work_unit_fingerprint": _non_empty_text(gate_report.get("work_unit_fingerprint")),
        }
    }


def _controller_route_context_for_publication_work_unit(
    *,
    gate_report: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
    source_eval_id: str | None,
) -> dict[str, Any] | None:
    publication_work_unit_payload = publication_work_units.derive_publication_work_units(
        dict(gate_report),
        specificity_targets=publication_work_units.specificity_targets_from_publication_eval(
            publication_eval_payload
        ),
    )
    next_work_unit = publication_work_unit_payload.get("next_work_unit")
    if not isinstance(next_work_unit, Mapping):
        return None
    work_unit_id = _non_empty_text(next_work_unit.get("unit_id"))
    if work_unit_id not in UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS:
        return None
    return {
        "controller_route_context": {
            "control_surface": "quality_repair_batch",
            "controller_action_type": StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value,
            "work_unit_id": work_unit_id,
            "requires_human_confirmation": False,
            "source_eval_id": source_eval_id,
            "gate_fingerprint": _non_empty_text(gate_report.get("gate_fingerprint")),
            "work_unit_fingerprint": _non_empty_text(publication_work_unit_payload.get("fingerprint")),
        }
    }


def _route_action_for_controller_context(route_context: Mapping[str, Any] | None) -> str:
    controller_route_context = (
        route_context.get("controller_route_context")
        if isinstance(route_context, Mapping)
        else None
    )
    if not isinstance(controller_route_context, Mapping):
        return "bundle_build"
    if _non_empty_text(controller_route_context.get("work_unit_id")) in UPSTREAM_PUBLISHABILITY_REPAIR_WORK_UNIT_IDS:
        return "paper_write"
    return "bundle_build"


def _merge_route_contexts(*contexts: Mapping[str, Any] | None) -> dict[str, Any] | None:
    merged: dict[str, Any] = {}
    for context in contexts:
        if isinstance(context, Mapping):
            merged.update(dict(context))
    return merged or None


def _canonical_paper_owner_surface_complete(paper_root: Path) -> bool:
    return all((paper_root / relpath).exists() for relpath in _CANONICAL_PAPER_OWNER_REQUIRED_SURFACES)


def _hydration_paper_owner_projection_inputs(projected_paper_root: Path) -> list[Path]:
    inputs = [projected_paper_root / relpath for relpath in _HYDRATION_PAPER_OWNER_INPUT_SURFACES]
    for pattern in _HYDRATION_PAPER_OWNER_INPUT_GLOBS:
        inputs.extend(sorted(projected_paper_root.glob(pattern)))
    return [path for path in inputs if path.is_file()]


def _default_canonical_paper_json_surface(
    *,
    relpath: Path,
    study_id: str,
    quest_id: str,
) -> dict[str, Any]:
    if relpath == Path("paper_bundle_manifest.json"):
        return {
            "schema_version": 1,
            "paper_branch": "paper/main",
            "bundle_inputs": {
                "compile_report_path": "paper/build/compile_report.json",
                "compiled_markdown_path": "paper/build/review_manuscript.md",
                "figure_catalog_path": "paper/figures/figure_catalog.json",
                "table_catalog_path": "paper/tables/table_catalog.json",
            },
            "owner_surface": {
                "status": "initialized_for_controller_quality_repair",
                "controller": "quality_repair_batch",
                "study_id": study_id,
                "quest_id": quest_id,
            },
        }
    if relpath == Path("medical_manuscript_blueprint.json"):
        return {"schema_version": 1, "status": "owner_surface_initialized", "sections": []}
    if relpath == Path("medical_prose_review.json"):
        return {"schema_version": 1, "status": "owner_surface_initialized", "findings": []}
    if relpath == Path("claim_evidence_map.json"):
        return {"schema_version": 1, "status": "owner_surface_initialized", "claims": []}
    if relpath == Path("display_registry.json"):
        return {"schema_version": 1, "status": "owner_surface_initialized", "displays": []}
    if relpath == Path("results_narrative_map.json"):
        return {"schema_version": 1, "status": "owner_surface_initialized", "sections": []}
    if relpath == Path("figure_semantics_manifest.json"):
        return {"schema_version": 1, "status": "owner_surface_initialized", "figures": []}
    if relpath == Path("figures/figure_catalog.json"):
        return {"schema_version": 1, "status": "owner_surface_initialized", "figures": []}
    if relpath == Path("tables/table_catalog.json"):
        return {"schema_version": 1, "status": "owner_surface_initialized", "tables": []}
    return {"schema_version": 1, "status": "owner_surface_initialized"}


def _copy_or_initialize_canonical_paper_surface(
    *,
    source_root: Path,
    target_root: Path,
    relpath: Path,
    study_id: str,
    quest_id: str,
) -> dict[str, Any]:
    target_path = target_root / relpath
    if target_path.exists():
        return {"relative_path": relpath.as_posix(), "status": "already_present"}
    source_path = source_root / relpath
    target_path.parent.mkdir(parents=True, exist_ok=True)
    if source_path.exists() and source_path.is_file():
        shutil.copy2(source_path, target_path)
        return {
            "relative_path": relpath.as_posix(),
            "status": "copied_from_quest_projection",
            "source_path": str(source_path.resolve()),
        }
    if relpath == Path("draft.md"):
        target_path.write_text(
            "# Manuscript Draft\n\nCanonical paper owner surface initialized for controller-owned quality repair.\n",
            encoding="utf-8",
        )
        return {"relative_path": relpath.as_posix(), "status": "initialized_owner_shell"}
    _write_json(
        target_path,
        _default_canonical_paper_json_surface(relpath=relpath, study_id=study_id, quest_id=quest_id),
    )
    return {"relative_path": relpath.as_posix(), "status": "initialized_owner_shell"}


def _prepare_canonical_paper_owner_surface_for_upstream_repair(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    quest_id: str,
    gate_state: Any,
    control_plane_route_gate: Mapping[str, Any],
) -> dict[str, Any]:
    if _non_empty_text(control_plane_route_gate.get("action")) != "paper_write":
        return {"status": "not_applicable", "reason": "route_action_not_paper_write"}

    canonical_paper_root = Path(study_root).expanduser().resolve() / "paper"
    if getattr(gate_state, "paper_root", None) is not None:
        existing_paper_root = Path(getattr(gate_state, "paper_root"))
        surface_results = [
            _copy_or_initialize_canonical_paper_surface(
                source_root=existing_paper_root,
                target_root=canonical_paper_root,
                relpath=relpath,
                study_id=study_id,
                quest_id=quest_id,
            )
            for relpath in _CANONICAL_PAPER_OWNER_REQUIRED_SURFACES
            if not (canonical_paper_root / relpath).exists()
        ]
        return {
            "status": "repaired_existing" if surface_results else "already_complete",
            "paper_root": str(canonical_paper_root),
            "surface_results": surface_results,
        }

    if _canonical_paper_owner_surface_complete(canonical_paper_root):
        return {"status": "already_complete", "paper_root": str(canonical_paper_root)}

    quest_root = profile.managed_runtime_quests_root / quest_id
    projected_paper_root = quest_root / "paper"
    canonical_projection_inputs = [
        projected_paper_root / relpath
        for relpath in _CANONICAL_PAPER_OWNER_PROJECTION_INPUT_SURFACES
        if (projected_paper_root / relpath).is_file()
    ]
    hydration_projection_inputs = _hydration_paper_owner_projection_inputs(projected_paper_root)
    if not canonical_projection_inputs and not hydration_projection_inputs:
        return {
            "status": "blocked_missing_projection",
            "paper_root": str(canonical_paper_root),
            "quest_projection_root": str(projected_paper_root.resolve()),
            "missing_reason": "quest paper projection has no canonical owner-surface inputs",
        }
    projection_input_status = (
        "canonical_projection_present"
        if canonical_projection_inputs
        else "hydration_projection_present"
    )
    surface_results = [
        _copy_or_initialize_canonical_paper_surface(
            source_root=projected_paper_root,
            target_root=canonical_paper_root,
            relpath=relpath,
            study_id=study_id,
            quest_id=quest_id,
        )
        for relpath in _CANONICAL_PAPER_OWNER_REQUIRED_SURFACES
    ]
    for dirname in ("build", "review", "submission_minimal"):
        (canonical_paper_root / dirname).mkdir(parents=True, exist_ok=True)

    manifest_payload = _read_json_object(canonical_paper_root / "paper_bundle_manifest.json")
    paper_branch = _non_empty_text(manifest_payload.get("paper_branch")) or "paper/main"
    paper_line_state_path = canonical_paper_root / "paper_line_state.json"
    if not paper_line_state_path.exists():
        _write_json(
            paper_line_state_path,
            {
                "schema_version": 1,
                "paper_branch": paper_branch,
                "paper_root": str(canonical_paper_root),
                "surface_owner": "study_canonical_paper_owner_surface",
                "controller": "quality_repair_batch",
                "study_id": study_id,
                "quest_id": quest_id,
            },
        )
        surface_results.append({"relative_path": "paper_line_state.json", "status": "initialized_owner_state"})

    return {
        "status": "materialized",
        "paper_root": str(canonical_paper_root),
        "quest_projection_root": str(projected_paper_root.resolve()),
        "projection_input_status": projection_input_status,
        "projection_input_count": len(canonical_projection_inputs) + len(hydration_projection_inputs),
        "surface_results": surface_results,
    }


def build_quality_repair_batch_recommended_action(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    quest_id: str,
    publication_eval_payload: dict[str, Any],
    gate_report: dict[str, Any],
) -> dict[str, Any] | None:
    verdict = publication_eval_payload.get("verdict")
    if not isinstance(verdict, dict) or _non_empty_text(verdict.get("overall_verdict")) != "blocked":
        return None
    if _non_empty_text(gate_report.get("status")) != "blocked":
        return None

    resolved_study_root = Path(study_root).expanduser().resolve()
    summary_payload = _read_quality_summary(study_root=resolved_study_root)
    if not summary_payload or not _quality_repair_required(summary_payload):
        return None

    current_eval_id = _non_empty_text(publication_eval_payload.get("eval_id"))
    latest_batch = _latest_batch_record(study_root=resolved_study_root)
    nested_gate_batch = latest_batch.get("gate_clearing_batch")
    if not isinstance(nested_gate_batch, dict):
        nested_gate_batch = {}
    if gate_clearing_batch_currentness.batch_closed_for_source_eval(
        nested_gate_batch,
        source_eval_id=current_eval_id,
    ):
        return None

    candidates = _repair_candidates(
        profile=profile,
        study_root=resolved_study_root,
        quest_id=quest_id,
        gate_report=gate_report,
        include_downstream_delivery=not bool(gate_report.get("bundle_tasks_downstream_only")),
    )
    if not candidates:
        return None

    publication_work_unit_payload = publication_work_units.derive_publication_work_units(gate_report)
    quality_closure_truth, quality_execution_lane = _quality_repair_context(summary_payload)
    route_target = (
        _non_empty_text(quality_execution_lane.get("route_target"))
        or _non_empty_text(quality_closure_truth.get("route_target"))
        or "review"
    )
    route_key_question = _non_empty_text(quality_execution_lane.get("route_key_question")) or (
        "Which deterministic quality repair is still blocking the publishability gate?"
    )
    route_rationale = (
        _non_empty_text(quality_execution_lane.get("summary"))
        or _non_empty_text(quality_closure_truth.get("summary"))
        or "Run deterministic quality repair units before replaying the publishability gate."
    )
    reason_bits = ["quality_closure_truth requires deterministic repair", *candidates]
    return {
        "action_id": f"quality-repair-batch::{resolved_study_root.name}::{current_eval_id or 'latest'}",
        "action_type": StudyDecisionType.ROUTE_BACK_SAME_LINE.value,
        "priority": "now",
        "reason": "Run one controller-owned quality repair batch before returning to publishability gate.",
        "route_target": route_target,
        "route_key_question": route_key_question,
        "route_rationale": route_rationale,
        "requires_controller_decision": True,
        "controller_action_type": StudyDecisionActionType.RUN_QUALITY_REPAIR_BATCH.value,
        "quality_repair_batch_reason": "; ".join(reason_bits),
        "work_unit_fingerprint": publication_work_unit_payload.get("fingerprint"),
        "gate_fingerprint": gate_report.get("gate_fingerprint"),
        "blocking_artifact_refs": gate_report.get("blocking_artifact_refs") or [],
        "blocking_work_units": publication_work_unit_payload.get("blocking_work_units") or [],
        "next_work_unit": publication_work_unit_payload.get("next_work_unit"),
    }


def run_quality_repair_batch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    quest_id: str,
    source: str = "med_autoscience",
    control_plane_route_context: Mapping[str, Any] | None = None,
    route_context: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    resolved_route_context = (
        control_plane_route_context
        or route_context
        or _runtime_control_plane_route_context(
            profile=profile,
            study_id=study_id,
            study_root=resolved_study_root,
        )
    )
    publication_eval_payload = read_publication_eval_latest(study_root=resolved_study_root)
    current_eval_id = _non_empty_text(publication_eval_payload.get("eval_id"))
    quest_root = profile.managed_runtime_quests_root / quest_id
    gate_state = gate_clearing_batch.publication_gate.build_gate_state(quest_root)
    gate_report = gate_clearing_batch.publication_gate.build_gate_report(gate_state)
    controller_route_context = _controller_route_context_for_gate(
        gate_report=gate_report,
        source_eval_id=current_eval_id,
    )
    if controller_route_context is None:
        controller_route_context = _controller_route_context_for_publication_work_unit(
            gate_report=gate_report,
            publication_eval_payload=publication_eval_payload,
            source_eval_id=current_eval_id,
        )
    resolved_route_context = _merge_route_contexts(
        resolved_route_context,
        controller_route_context,
    )
    control_plane_route_gate = assert_control_plane_route_authorized(
        _route_action_for_controller_context(resolved_route_context),
        {"projection_only": True} if resolved_route_context is None else resolved_route_context,
    )
    paper_owner_surface_prepare = _prepare_canonical_paper_owner_surface_for_upstream_repair(
        profile=profile,
        study_id=study_id,
        study_root=resolved_study_root,
        quest_id=quest_id,
        gate_state=gate_state,
        control_plane_route_gate=control_plane_route_gate,
    )
    summary_payload = _read_quality_summary(study_root=resolved_study_root)
    quality_closure_truth, quality_execution_lane = _quality_repair_context(summary_payload)
    source_summary_id = _non_empty_text(summary_payload.get("summary_id"))
    latest_batch = _latest_batch_record(study_root=resolved_study_root)
    nested_gate_batch = latest_batch.get("gate_clearing_batch")
    if not isinstance(nested_gate_batch, dict):
        nested_gate_batch = {}
    if gate_clearing_batch_currentness.batch_closed_for_source_eval(
        nested_gate_batch,
        source_eval_id=current_eval_id,
    ):
        return {
            "ok": True,
            "status": "skipped_duplicate_eval",
            "source_eval_id": current_eval_id,
            "latest_record_path": str(stable_quality_repair_batch_path(study_root=resolved_study_root)),
            "control_plane_route_gate": control_plane_route_gate,
        }

    gate_clearing_result = gate_clearing_batch.run_gate_clearing_batch(
        profile=profile,
        study_id=study_id,
        study_root=resolved_study_root,
        quest_id=quest_id,
        source=source,
        control_plane_route_context=resolved_route_context,
    )
    gate_clearing_execution_summary = (
        dict(gate_clearing_result.get("execution_summary"))
        if isinstance(gate_clearing_result.get("execution_summary"), Mapping)
        else None
    )
    record = {
        "schema_version": SCHEMA_VERSION,
        "source_eval_id": current_eval_id,
        "source_eval_artifact_path": str(
            (resolved_study_root / "artifacts" / "publication_eval" / "latest.json").resolve()
        ),
        "source_summary_id": source_summary_id,
        "source_summary_artifact_path": str(_quality_summary_path(study_root=resolved_study_root).resolve()),
        "status": _non_empty_text(gate_clearing_result.get("status")) or "executed",
        "ok": bool(gate_clearing_result.get("ok")),
        "quest_id": quest_id,
        "study_id": study_id,
        "quality_closure_state": _non_empty_text(quality_closure_truth.get("state")),
        "quality_execution_lane_id": _non_empty_text(quality_execution_lane.get("lane_id")),
        "gate_clearing_batch": gate_clearing_result,
        "gate_clearing_execution_summary": gate_clearing_execution_summary,
        "control_plane_route_gate": control_plane_route_gate,
        "paper_owner_surface_prepare": paper_owner_surface_prepare,
    }
    record_path = stable_quality_repair_batch_path(study_root=resolved_study_root)
    _write_json(record_path, record)
    return {
        "ok": bool(record["ok"]),
        "status": str(record["status"]),
        "record_path": str(record_path),
        **record,
    }
