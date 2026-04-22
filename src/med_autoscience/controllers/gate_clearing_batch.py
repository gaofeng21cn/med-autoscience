from __future__ import annotations

import json
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import yaml

from med_autoscience.controllers import display_surface_materialization, publication_gate
from med_autoscience.controllers import study_delivery_sync, submission_minimal
from med_autoscience.controllers import study_runtime_router
from med_autoscience.publication_eval_latest import read_publication_eval_latest
from med_autoscience.profiles import WorkspaceProfile, load_profile
from med_autoscience.runtime_transport import med_deepscientist as med_deepscientist_transport
from med_autoscience.study_charter import materialize_study_charter


SCHEMA_VERSION = 1
STABLE_GATE_CLEARING_BATCH_RELATIVE_PATH = Path("artifacts/controller/gate_clearing_batch/latest.json")
REPAIRABLE_MEDICAL_SURFACE_BLOCKERS = frozenset(
    {
        "missing_medical_story_contract",
        "claim_evidence_map_missing_or_incomplete",
        "figure_catalog_missing_or_incomplete",
        "table_catalog_missing_or_incomplete",
        "required_display_catalog_coverage_incomplete",
        "results_narrative_map_missing_or_incomplete",
        "derived_analysis_manifest_missing_or_incomplete",
    }
)
_BUNDLE_STAGE_CURRENT_REQUIRED_ACTIONS = frozenset({"continue_bundle_stage", "complete_bundle_stage"})
_BUNDLE_STAGE_GATE_BLOCKERS = frozenset(
    {
        "stale_study_delivery_mirror",
        "submission_surface_qc_failure_present",
        "submission_hardening_incomplete",
    }
)


@dataclass(frozen=True)
class GateClearingRepairUnit:
    unit_id: str
    label: str
    parallel_safe: bool
    run: Callable[[], dict[str, Any]]


def stable_gate_clearing_batch_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / STABLE_GATE_CLEARING_BATCH_RELATIVE_PATH


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text:
            items.append(text)
    return items


def _quest_root(profile: WorkspaceProfile, *, quest_id: str) -> Path:
    return profile.med_deepscientist_runtime_root / "quests" / quest_id


def resolve_profile_for_study_root(study_root: Path) -> WorkspaceProfile | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    workspace_root = resolved_study_root.parent.parent
    config_env_path = workspace_root / "ops" / "medautoscience" / "config.env"
    profile_path: Path | None = None
    if config_env_path.exists():
        configured = med_deepscientist_transport._read_optional_config_env_value(
            path=config_env_path,
            key="MED_AUTOSCIENCE_PROFILE",
        )
        if configured is not None:
            profile_path = Path(configured).expanduser().resolve()
    if profile_path is None:
        candidates = sorted((workspace_root / "ops" / "medautoscience" / "profiles").glob("*.local.toml"))
        if len(candidates) == 1:
            profile_path = candidates[0].resolve()
    if profile_path is None or not profile_path.exists():
        return None
    return load_profile(profile_path)


def _latest_scientific_anchor_mapping_path(*, quest_root: Path) -> Path | None:
    worktrees_root = quest_root / ".ds" / "worktrees"
    candidates = sorted(
        worktrees_root.glob("analysis-*/experiments/analysis/*/*/outputs/scientific_anchor_mapping.json"),
        key=lambda path: path.stat().st_mtime if path.exists() else 0.0,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _current_workspace_root(*, quest_root: Path, default: Path) -> Path:
    research_state = _read_json(quest_root / ".ds" / "research_state.json")
    raw = _non_empty_text(research_state.get("current_workspace_root"))
    if raw is None:
        return default
    return Path(raw).expanduser().resolve()


def _latest_batch_record(*, study_root: Path) -> dict[str, Any]:
    return _read_json(stable_gate_clearing_batch_path(study_root=study_root))


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


def _bundle_stage_repair_requested(*, gate_report: dict[str, Any]) -> bool:
    current_required_action = str(gate_report.get("current_required_action") or "").strip()
    if current_required_action in _BUNDLE_STAGE_CURRENT_REQUIRED_ACTIONS:
        return True
    return bool(_gate_blockers(gate_report) & _BUNDLE_STAGE_GATE_BLOCKERS)


def _bundle_stage_batch_action(
    *,
    source_action: dict[str, Any] | None,
    gate_report: dict[str, Any],
) -> dict[str, Any]:
    current_required_action = str(gate_report.get("current_required_action") or "").strip()
    reason = (
        str((source_action or {}).get("reason") or "").strip()
        or str(gate_report.get("controller_stage_note") or "").strip()
        or "Run one controller-owned finalize/submission repair batch before returning to the same paper line."
    )
    route_rationale = (
        str((source_action or {}).get("route_rationale") or "").strip()
        or str(gate_report.get("controller_stage_note") or "").strip()
        or "The remaining bundle-stage blockers are deterministic finalize/submission repairs."
    )
    route_key_question = (
        str((source_action or {}).get("route_key_question") or "").strip()
        or "What is the narrowest finalize or submission-bundle step still required on the current paper line?"
    )
    priority = str((source_action or {}).get("priority") or "").strip() or "now"
    requires_controller_decision = bool((source_action or {}).get("requires_controller_decision"))
    if source_action is None:
        requires_controller_decision = True
    return {
        **(source_action or {}),
        "action_type": "route_back_same_line",
        "priority": priority,
        "reason": reason,
        "route_target": "finalize",
        "route_key_question": route_key_question,
        "route_rationale": route_rationale,
        "requires_controller_decision": requires_controller_decision,
        "current_required_action": current_required_action or None,
    }


def _eligible_mapping_payload(*, quest_root: Path, study_root: Path) -> tuple[Path | None, dict[str, Any]]:
    mapping_path = _latest_scientific_anchor_mapping_path(quest_root=quest_root)
    if mapping_path is None:
        return None, {}
    stable_charter_path = Path(study_root).expanduser().resolve() / "artifacts" / "controller" / "study_charter.json"
    stable_charter = _read_json(stable_charter_path)
    if _string_list(stable_charter.get("scientific_followup_questions")) and _string_list(
        stable_charter.get("explanation_targets")
    ):
        return mapping_path, {}
    payload = _read_json(mapping_path)
    if not payload:
        return mapping_path, {}
    proposed_questions = _string_list(payload.get("proposed_scientific_followup_questions"))
    proposed_targets = _string_list(payload.get("proposed_explanation_targets"))
    if not proposed_questions or not proposed_targets:
        return mapping_path, {}
    return mapping_path, payload


def build_gate_clearing_batch_recommended_action(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    quest_id: str,
    publication_eval_payload: dict[str, Any],
    gate_report: dict[str, Any],
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
    current_required_action = str(gate_report.get("current_required_action") or "").strip()

    medical_surface_blockers = {
        str(item or "").strip()
        for item in (gate_report.get("medical_publication_surface_named_blockers") or [])
        if str(item or "").strip()
    }
    repairable_surface = bool(medical_surface_blockers & REPAIRABLE_MEDICAL_SURFACE_BLOCKERS)
    stale_delivery = "stale_study_delivery_mirror" in gate_blockers
    bundle_stage_repair = _bundle_stage_repair_requested(gate_report=gate_report)
    quest_root = _quest_root(profile, quest_id=quest_id)
    mapping_path, mapping_payload = _eligible_mapping_payload(
        quest_root=quest_root,
        study_root=study_root,
    )
    anchor_repairable = bool(mapping_payload)
    if not any((repairable_surface, stale_delivery, anchor_repairable, bundle_stage_repair)):
        return None
    if (repairable_surface or anchor_repairable) and bounded_analysis_action is None:
        return None

    latest_batch = _latest_batch_record(study_root=study_root)
    current_eval_id = str(publication_eval_payload.get("eval_id") or "").strip()
    if str(latest_batch.get("source_eval_id") or "").strip() == current_eval_id:
        return None

    if anchor_repairable or repairable_surface:
        selected_action = dict(bounded_analysis_action or {})
    elif bundle_stage_repair:
        selected_action = _bundle_stage_batch_action(
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
    }


def _freeze_scientific_anchor_fields(
    *,
    study_root: Path,
    study_id: str,
    profile: WorkspaceProfile,
    mapping_path: Path,
) -> dict[str, Any]:
    study_yaml_path = Path(study_root).expanduser().resolve() / "study.yaml"
    study_payload = _read_yaml(study_yaml_path)
    mapping_payload = _read_json(mapping_path)
    proposed_questions = _string_list(mapping_payload.get("proposed_scientific_followup_questions"))
    proposed_targets = _string_list(mapping_payload.get("proposed_explanation_targets"))
    clinician_target = _non_empty_text(mapping_payload.get("clinician_facing_interpretation_target"))
    if clinician_target is not None and clinician_target not in proposed_targets:
        proposed_targets.append(clinician_target)
    if not proposed_questions or not proposed_targets:
        return {
            "status": "skipped",
            "reason": "scientific anchor mapping did not expose non-empty proposed targets",
            "mapping_path": str(mapping_path),
        }
    study_payload["scientific_followup_questions"] = proposed_questions
    study_payload["explanation_targets"] = proposed_targets
    _write_yaml(study_yaml_path, study_payload)
    charter_ref = materialize_study_charter(
        study_root=study_root,
        study_id=study_id,
        study_payload=study_payload,
        execution=study_runtime_router._execution_payload(study_payload, profile=profile),
        required_first_anchor=_non_empty_text((study_payload.get("execution") or {}).get("required_first_anchor")),
    )
    return {
        "status": "updated",
        "mapping_path": str(mapping_path),
        "study_yaml_path": str(study_yaml_path),
        "charter_ref": charter_ref,
        "scientific_followup_question_count": len(proposed_questions),
        "explanation_target_count": len(proposed_targets),
    }


def _repair_paper_live_paths(
    *,
    profile: WorkspaceProfile,
    quest_id: str,
    workspace_root: Path,
    current_workspace_root: Path,
) -> dict[str, Any]:
    launcher = med_deepscientist_transport._read_config_env_value(
        path=profile.med_deepscientist_runtime_root.parent / "config.env",
        key="MED_DEEPSCIENTIST_LAUNCHER",
    )
    command = [
        launcher,
        "--home",
        str(profile.managed_runtime_home),
        "repair",
        "paper-live-paths",
        "--quest-id",
        quest_id,
        "--workspace-root",
        str(workspace_root),
        "--current-workspace-root",
        str(current_workspace_root),
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    payload = json.loads(completed.stdout or "{}")
    if not isinstance(payload, dict):
        raise RuntimeError("paper-live-path repair returned a non-object payload")
    return payload


def _materialize_display_surface(*, paper_root: Path) -> dict[str, Any]:
    return display_surface_materialization.materialize_display_surface(paper_root=paper_root)


def _run_workspace_display_repair_script(*, paper_root: Path) -> dict[str, Any]:
    script_path = paper_root / "build" / "generate_display_exports.py"
    if not script_path.exists():
        return {
            "status": "missing",
            "script_path": str(script_path),
        }
    completed = subprocess.run(
        [shutil.which("python3") or sys.executable, str(script_path)],
        cwd=str(paper_root.parent),
        check=True,
        capture_output=True,
        text=True,
    )
    return {
        "status": "updated",
        "script_path": str(script_path),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def _create_submission_minimal_package(*, paper_root: Path, profile: WorkspaceProfile) -> dict[str, Any]:
    return submission_minimal.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile=profile.default_publication_profile,
        citation_style=profile.default_citation_style,
    )


def run_gate_clearing_batch(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    quest_id: str,
    source: str = "med_autoscience",
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    quest_root = _quest_root(profile, quest_id=quest_id)
    gate_state = publication_gate.build_gate_state(quest_root)
    gate_report = publication_gate.build_gate_report(gate_state)
    publication_eval_payload = read_publication_eval_latest(study_root=resolved_study_root)
    latest_batch = _latest_batch_record(study_root=resolved_study_root)
    current_eval_id = str(publication_eval_payload.get("eval_id") or "").strip()
    if str(latest_batch.get("source_eval_id") or "").strip() == current_eval_id:
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
    bundle_stage_repair = _bundle_stage_repair_requested(gate_report=gate_report)

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
    if str(gate_report.get("medical_publication_surface_status") or "").strip() == "blocked":
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
        display_repair_script_path = paper_root / "build" / "generate_display_exports.py"
        if display_repair_script_path.exists():
            repair_units.append(
                GateClearingRepairUnit(
                    unit_id="workspace_display_repair_script",
                    label="Run the workspace-authored display repair script before gate replay",
                    parallel_safe=True,
                    run=lambda: _run_workspace_display_repair_script(paper_root=paper_root),
                )
            )
        else:
            repair_units.append(
                GateClearingRepairUnit(
                    unit_id="materialize_display_surface",
                    label="Refresh display catalogs and generated paper-facing exports",
                    parallel_safe=True,
                    run=lambda: _materialize_display_surface(paper_root=paper_root),
                )
            )
    if not repair_units and str(gate_report.get("study_delivery_status") or "").strip().startswith("stale"):
        # Let publication_gate.run_controller(apply=True) own stale delivery refresh even when
        # there are no other deterministic repairs to launch in parallel.
        repair_units = []

    if not repair_units and not bundle_stage_repair and not str(gate_report.get("study_delivery_status") or "").strip().startswith("stale"):
        return {
            "ok": False,
            "status": "no_repair_units",
            "source_eval_id": current_eval_id,
            "gate_blockers": sorted(gate_blockers),
        }

    unit_results: list[dict[str, Any]] = []
    if repair_units:
        with ThreadPoolExecutor(max_workers=len(repair_units)) as executor:
            futures = {executor.submit(unit.run): unit for unit in repair_units}
            for future, unit in ((future, futures[future]) for future in futures):
                try:
                    result = future.result()
                    unit_results.append(
                        {
                            "unit_id": unit.unit_id,
                            "label": unit.label,
                            "parallel_safe": unit.parallel_safe,
                            "status": str(result.get("status") or "ok"),
                            "result": result,
                        }
                    )
                except Exception as exc:
                    unit_results.append(
                        {
                            "unit_id": unit.unit_id,
                            "label": unit.label,
                            "parallel_safe": unit.parallel_safe,
                            "status": "failed",
                            "error": str(exc),
                        }
                    )

    if bundle_stage_repair:
        try:
            result = _create_submission_minimal_package(paper_root=paper_root, profile=profile)
            unit_results.append(
                {
                    "unit_id": "create_submission_minimal_package",
                    "label": "Regenerate submission-minimal assets before gate replay",
                    "parallel_safe": False,
                    "status": "updated",
                    "result": result,
                }
            )
        except Exception as exc:
            unit_results.append(
                {
                    "unit_id": "create_submission_minimal_package",
                    "label": "Regenerate submission-minimal assets before gate replay",
                    "parallel_safe": False,
                    "status": "failed",
                    "error": str(exc),
                }
            )

    gate_replay = publication_gate.run_controller(
        quest_root=quest_root,
        apply=True,
        source=source,
    )
    record = {
        "schema_version": SCHEMA_VERSION,
        "source_eval_id": current_eval_id,
        "source_eval_artifact_path": str(
            (resolved_study_root / "artifacts" / "publication_eval" / "latest.json").resolve()
        ),
        "status": "executed",
        "quest_id": quest_id,
        "study_id": study_id,
        "paper_root": str(paper_root),
        "workspace_root": str(paper_root.parent),
        "current_workspace_root": str(current_workspace_root),
        "gate_blockers": sorted(gate_blockers),
        "unit_results": unit_results,
        "gate_replay": gate_replay,
    }
    record_path = stable_gate_clearing_batch_path(study_root=resolved_study_root)
    _write_json(record_path, record)
    return {
        "ok": True,
        "status": "executed",
        "record_path": str(record_path),
        **record,
    }
