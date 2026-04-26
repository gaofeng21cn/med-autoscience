from __future__ import annotations

import hashlib
import json
from importlib import import_module
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import yaml

from med_autoscience.publication_eval_latest import read_publication_eval_latest
from med_autoscience.profiles import WorkspaceProfile, load_profile
from med_autoscience.runtime_transport import med_deepscientist as med_deepscientist_transport
from med_autoscience.study_charter import materialize_study_charter
from med_autoscience.controllers.gate_clearing_batch_blockers import (
    REPAIRABLE_MEDICAL_SURFACE_BLOCKERS,
    medical_surface_repair_blockers,
)
from med_autoscience.controllers.gate_clearing_batch_fingerprints import (
    globbed_path_fingerprints as _globbed_path_fingerprints,
    path_fingerprint as _path_fingerprint,
    path_fingerprints as _path_fingerprints,
)
from med_autoscience.controllers import gate_clearing_batch_package_freshness
from med_autoscience.controllers import gate_clearing_batch_submission
from med_autoscience.controllers import gate_clearing_batch_scheduler
from med_autoscience.controllers import publication_work_units
from med_autoscience.controllers import publication_work_unit_lifecycle
from med_autoscience.controllers.gate_clearing_batch_work_units import (
    derived_next_publication_work_unit,
    explicit_next_publication_work_unit,
    filter_repair_units_for_publication_work_unit,
)


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


@dataclass(frozen=True)
class GateClearingRepairUnit:
    unit_id: str
    label: str
    parallel_safe: bool
    run: Callable[[], dict[str, Any]]
    depends_on: tuple[str, ...] = ()


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


_clock_snapshot = publication_work_unit_lifecycle.clock_snapshot


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        return {}
    return payload


def _write_yaml(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(payload, allow_unicode=True, sort_keys=False), encoding="utf-8")


def _parse_json_object_from_cli_stdout(stdout: str) -> dict[str, Any]:
    text = (stdout or "").strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        payload = None
        for index, char in enumerate(text):
            if char != "{":
                continue
            try:
                candidate, consumed = decoder.raw_decode(text[index:])
            except json.JSONDecodeError:
                continue
            if text[index + consumed :].strip():
                continue
            payload = candidate
            break
        if payload is None:
            raise
    if not isinstance(payload, dict):
        raise RuntimeError("CLI returned a non-object JSON payload")
    return payload


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


def _candidate_values_include_root(
    *,
    workspace_root: Path,
    candidate_values: list[object],
    root: Path,
) -> bool:
    root_resolved = root.resolve()
    for candidate in candidate_values:
        if not isinstance(candidate, str):
            continue
        normalized = candidate.strip()
        if not normalized:
            continue
        try:
            submission_minimal.resolve_relpath(workspace_root, normalized).resolve().relative_to(root_resolved)
        except ValueError:
            continue
        return True
    return False


def _catalog_asset_fingerprints(
    *,
    workspace_root: Path,
    catalog_payload: dict[str, Any],
    item_key: str,
    resolve_source_paths: Callable[[dict[str, Any]], list[str]],
    limit: int = 128,
) -> list[dict[str, Any]]:
    items = catalog_payload.get(item_key)
    if not isinstance(items, list):
        return []
    fingerprints: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        for raw_path in resolve_source_paths(item):
            normalized = str(raw_path or "").strip()
            if not normalized:
                continue
            resolved = submission_minimal.resolve_relpath(workspace_root, normalized).expanduser().resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            fingerprint = _path_fingerprint(resolved)
            if fingerprint is not None:
                fingerprints.append(fingerprint)
            if len(fingerprints) >= limit:
                return fingerprints
    return fingerprints


def _submission_minimal_fingerprint_payload(
    *,
    paper_root: Path,
    gate_report: dict[str, Any],
    profile: WorkspaceProfile | None,
) -> dict[str, Any]:
    bundle_manifest_path = paper_root / "paper_bundle_manifest.json"
    payload: dict[str, Any] = {
        "unit_id": "create_submission_minimal_package",
        "current_required_action": _non_empty_text(gate_report.get("current_required_action")),
        "gate_blockers": sorted(_gate_blockers(gate_report)),
        "paper_bundle_manifest": _path_fingerprint(bundle_manifest_path),
        "display_pack_lock": _path_fingerprint(paper_root / "build" / "display_pack_lock.json"),
    }
    if profile is not None:
        payload["requested_publication_profile"] = profile.default_publication_profile
        payload["requested_citation_style"] = profile.default_citation_style
    workspace_root = submission_minimal.workspace_root_from_paper_root(paper_root)
    if not bundle_manifest_path.exists():
        return payload
    try:
        bundle_manifest = submission_minimal.load_json(bundle_manifest_path)
    except Exception as exc:
        payload["bundle_manifest_error"] = str(exc)
        return payload

    try:
        requested_publication_profile = (
            profile.default_publication_profile
            if profile is not None
            else submission_minimal.GENERAL_MEDICAL_JOURNAL_PROFILE
        )
        requested_citation_style = profile.default_citation_style if profile is not None else "auto"
        profile_config = submission_minimal.resolve_publication_profile_config(
            publication_profile=requested_publication_profile,
            citation_style=requested_citation_style,
        )
        payload["resolved_publication_profile"] = profile_config.publication_profile
        payload["profile_artifacts"] = _path_fingerprints(
            profile_config.csl_path,
            profile_config.reference_doc_path,
            profile_config.supplementary_reference_doc_path,
        )
    except Exception as exc:
        payload["profile_config_error"] = str(exc)
        return payload

    try:
        compile_report_path = submission_minimal.resolve_relpath(
            workspace_root,
            submission_minimal.resolve_bundle_input_path(
                bundle_manifest=bundle_manifest,
                key="compile_report_path",
            ),
        )
        figure_catalog_path = submission_minimal.resolve_relpath(
            workspace_root,
            submission_minimal.resolve_bundle_input_path(
                bundle_manifest=bundle_manifest,
                key="figure_catalog_path",
                fallback="paper/figures/figure_catalog.json",
            ),
        )
        table_catalog_path = submission_minimal.resolve_relpath(
            workspace_root,
            submission_minimal.resolve_bundle_input_path(
                bundle_manifest=bundle_manifest,
                key="table_catalog_path",
                fallback="paper/tables/table_catalog.json",
            ),
        )
    except Exception as exc:
        payload["bundle_inputs_error"] = str(exc)
        return payload
    payload["compile_report"] = _path_fingerprint(compile_report_path)
    payload["figure_catalog"] = _path_fingerprint(figure_catalog_path)
    payload["table_catalog"] = _path_fingerprint(table_catalog_path)

    compile_report: dict[str, Any] = {}
    figure_catalog: dict[str, Any] = {}
    table_catalog: dict[str, Any] = {}
    try:
        compile_report = submission_minimal.load_json(compile_report_path)
    except Exception as exc:
        payload["compile_report_error"] = str(exc)
    try:
        figure_catalog = submission_minimal.load_json(figure_catalog_path)
    except Exception as exc:
        payload["figure_catalog_error"] = str(exc)
    try:
        table_catalog = submission_minimal.load_json(table_catalog_path)
    except Exception as exc:
        payload["table_catalog_error"] = str(exc)

    try:
        submission_root = submission_minimal.resolve_output_root(
            paper_root=paper_root,
            publication_profile=profile_config.publication_profile,
        )
        payload["submission_root"] = _path_fingerprint(submission_root)
        payload["submission_outputs"] = _path_fingerprints(
            submission_root / "manuscript.docx",
            submission_root / "paper.pdf",
            submission_root / "submission_manifest.json",
            submission_root / "README.md",
        )
        excluded_compiled_source_roots = submission_minimal.resolve_submission_compiled_source_excluded_roots(
            paper_root=paper_root,
            workspace_root=workspace_root,
            submission_root=submission_root,
            bundle_manifest=bundle_manifest,
            compile_report=compile_report,
            exclude_live_submission_root_for_markdown_candidates=True,
        )
        compiled_markdown_path = submission_minimal.resolve_compiled_markdown_path(
            workspace_root=workspace_root,
            bundle_manifest=bundle_manifest,
            compile_report=compile_report,
            excluded_roots=excluded_compiled_source_roots,
        )
        compiled_pdf_path = submission_minimal.resolve_compiled_pdf_path(
            workspace_root=workspace_root,
            bundle_manifest=bundle_manifest,
            compile_report=compile_report,
            excluded_roots=excluded_compiled_source_roots,
        )
        payload["compiled_markdown"] = _path_fingerprint(compiled_markdown_path)
        payload["compiled_pdf"] = _path_fingerprint(compiled_pdf_path)
    except Exception as exc:
        payload["compiled_surface_error"] = str(exc)

    payload["figure_assets"] = _catalog_asset_fingerprints(
        workspace_root=workspace_root,
        catalog_payload=figure_catalog,
        item_key="figures",
        resolve_source_paths=submission_minimal.resolve_figure_source_paths,
    )
    payload["table_assets"] = _catalog_asset_fingerprints(
        workspace_root=workspace_root,
        catalog_payload=table_catalog,
        item_key="tables",
        resolve_source_paths=submission_minimal.resolve_table_source_paths,
    )
    return payload


def _repair_unit_fingerprint(
    *,
    unit_id: str,
    paper_root: Path,
    gate_report: dict[str, Any],
    profile: WorkspaceProfile | None = None,
) -> str | None:
    payload: dict[str, Any] | None
    if unit_id == "materialize_display_surface":
        payload = {
            "unit_id": unit_id,
            "medical_publication_surface_status": _non_empty_text(gate_report.get("medical_publication_surface_status")),
            "medical_publication_surface_named_blockers": sorted(
                str(item or "").strip()
                for item in (gate_report.get("medical_publication_surface_named_blockers") or [])
                if str(item or "").strip()
            ),
            "display_registry": _path_fingerprint(paper_root / "display_registry.json"),
            "manuscript_assets": _globbed_path_fingerprints(
                paper_root,
                "figures/*.json",
                "tables/*.json",
                "figures/*.csv",
                "tables/*.csv",
                "results/*.json",
            ),
        }
    elif unit_id == "workspace_display_repair_script":
        payload = {
            "unit_id": unit_id,
            "medical_publication_surface_status": _non_empty_text(gate_report.get("medical_publication_surface_status")),
            "medical_publication_surface_named_blockers": sorted(
                str(item or "").strip()
                for item in (gate_report.get("medical_publication_surface_named_blockers") or [])
                if str(item or "").strip()
            ),
            "script": _path_fingerprint(paper_root / "build" / "generate_display_exports.py"),
            "display_registry": _path_fingerprint(paper_root / "display_registry.json"),
        }
    elif unit_id == "sync_submission_minimal_delivery":
        payload = {
            "unit_id": unit_id,
            "study_delivery_status": gate_clearing_batch_submission.study_delivery_status(gate_report),
            "study_delivery_stale_reason": gate_clearing_batch_submission.study_delivery_stale_reason(gate_report),
            "study_delivery_manifest_path": _non_empty_text(gate_report.get("study_delivery_manifest_path")),
            "study_delivery_current_package_root": _non_empty_text(gate_report.get("study_delivery_current_package_root")),
            "study_delivery_current_package_zip": _non_empty_text(gate_report.get("study_delivery_current_package_zip")),
            "study_delivery_missing_source_paths": _string_list(gate_report.get("study_delivery_missing_source_paths")),
            "submission_minimal_manifest": _path_fingerprint(paper_root / "submission_minimal" / "submission_manifest.json"),
            "submission_minimal_assets": _globbed_path_fingerprints(
                paper_root / "submission_minimal",
                "*.docx",
                "*.pdf",
                "*.json",
                "*.zip",
            ),
        }
    elif unit_id == "create_submission_minimal_package":
        payload = _submission_minimal_fingerprint_payload(
            paper_root=paper_root,
            gate_report=gate_report,
            profile=profile,
        )
    else:
        payload = None
    if payload is None:
        return None
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _latest_unit_result(latest_batch: dict[str, Any], *, unit_id: str) -> dict[str, Any] | None:
    for item in (latest_batch.get("unit_results") or []):
        if not isinstance(item, dict):
            continue
        if _non_empty_text(item.get("unit_id")) != unit_id:
            continue
        return item
    return None


def _latest_unit_status(latest_batch: dict[str, Any], *, unit_id: str) -> str | None:
    item = _latest_unit_result(latest_batch, unit_id=unit_id)
    if item is None:
        return None
    return _non_empty_text(item.get("status"))


def _unit_status_is_success(status: str | None) -> bool:
    return status not in {
        None,
        "failed",
        "missing",
        "skipped_failed_dependency",
        "skipped_matching_unit_fingerprint",
        "skipped_authority_not_settled",
    }


def _latest_unit_success_status(latest_batch: dict[str, Any], *, unit_id: str) -> str | None:
    item = _latest_unit_result(latest_batch, unit_id=unit_id)
    if item is None:
        return None
    last_success_status = _non_empty_text(item.get("last_success_status"))
    if last_success_status is not None:
        return last_success_status
    status = _non_empty_text(item.get("status"))
    if _unit_status_is_success(status):
        return status
    return None


def _latest_unit_fingerprint(latest_batch: dict[str, Any], *, unit_id: str) -> str | None:
    payload = latest_batch.get("unit_fingerprints")
    if not isinstance(payload, dict):
        return None
    return _non_empty_text(payload.get(unit_id))


def _can_skip_repair_unit(
    latest_batch: dict[str, Any],
    *,
    unit_id: str,
    unit_fingerprint: str | None,
) -> bool:
    if unit_fingerprint is None:
        return False
    previous_fingerprint = _latest_unit_fingerprint(latest_batch, unit_id=unit_id)
    if previous_fingerprint != unit_fingerprint:
        return False
    return _latest_unit_success_status(latest_batch, unit_id=unit_id) is not None


def _unit_status_blocks_dependents(status: str | None) -> bool:
    return status in {"failed", "missing", "skipped_failed_dependency", "skipped_authority_not_settled"}


def _existing_dependency_ids(
    repair_units: list[GateClearingRepairUnit],
    *candidate_unit_ids: str,
) -> tuple[str, ...]:
    existing_ids = {unit.unit_id for unit in repair_units}
    return tuple(unit_id for unit_id in candidate_unit_ids if unit_id in existing_ids)


def _run_repair_unit(
    *,
    unit: GateClearingRepairUnit,
    latest_batch: dict[str, Any],
    paper_root: Path,
    gate_report: dict[str, Any],
    profile: WorkspaceProfile,
) -> tuple[dict[str, Any], str | None]:
    unit_fingerprint = _repair_unit_fingerprint(
        unit_id=unit.unit_id,
        paper_root=paper_root,
        gate_report=gate_report,
        profile=profile,
    )
    item: dict[str, Any]
    if _can_skip_repair_unit(latest_batch, unit_id=unit.unit_id, unit_fingerprint=unit_fingerprint):
        previous_status = _latest_unit_status(latest_batch, unit_id=unit.unit_id)
        last_success_status = _latest_unit_success_status(latest_batch, unit_id=unit.unit_id)
        item = {
            "unit_id": unit.unit_id,
            "label": unit.label,
            "parallel_safe": unit.parallel_safe,
            "status": "skipped_matching_unit_fingerprint",
            "previous_status": previous_status,
            **publication_work_unit_lifecycle.instant_timing(clock=_clock_snapshot),
        }
        if last_success_status is not None:
            item["last_success_status"] = last_success_status
    else:
        started_ns, started_at = _clock_snapshot()
        try:
            result = unit.run()
            finished_ns, finished_at = _clock_snapshot()
            timing = {
                "started_at": started_at,
                "finished_at": finished_at,
                "duration_seconds": publication_work_unit_lifecycle.duration_seconds(started_ns, finished_ns),
            }
            item = {
                "unit_id": unit.unit_id,
                "label": unit.label,
                "parallel_safe": unit.parallel_safe,
                "status": str(result.get("status") or "ok"),
                "result": result,
                **timing,
            }
            publication_work_unit_lifecycle.copy_step_surface_metadata(item, result)
            if _unit_status_is_success(_non_empty_text(item.get("status"))):
                item["last_success_status"] = item["status"]
        except Exception as exc:
            item = {
                "unit_id": unit.unit_id,
                "label": unit.label,
                "parallel_safe": unit.parallel_safe,
                "status": "failed",
                "error": str(exc),
            }
            finished_ns, finished_at = _clock_snapshot()
            item.update(
                {
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "duration_seconds": publication_work_unit_lifecycle.duration_seconds(started_ns, finished_ns),
                }
            )
    if unit.depends_on:
        item["depends_on"] = list(unit.depends_on)
    if unit_fingerprint is not None:
        item["fingerprint"] = unit_fingerprint
    return item, unit_fingerprint


def _execute_repair_units(
    *,
    repair_units: list[GateClearingRepairUnit],
    latest_batch: dict[str, Any],
    paper_root: Path,
    gate_report: dict[str, Any],
    profile: WorkspaceProfile,
) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, int]]:
    unit_results_by_id: dict[str, dict[str, Any]] = {}
    unit_fingerprints: dict[str, str] = {}
    execution_summary = {
        "parallel_wave_count": 0,
        "parallel_unit_count": 0,
        "sequential_unit_count": 0,
        "skipped_dependency_unit_count": 0,
    }
    pending_units = list(repair_units)
    while pending_units:
        remaining_units: list[GateClearingRepairUnit] = []
        ready_parallel_units: list[GateClearingRepairUnit] = []
        ready_sequential_units: list[GateClearingRepairUnit] = []
        for unit in pending_units:
            dependency_statuses = {
                dependency_id: _non_empty_text((unit_results_by_id.get(dependency_id) or {}).get("status"))
                for dependency_id in unit.depends_on
                if dependency_id in unit_results_by_id
            }
            failed_dependencies = [
                dependency_id
                for dependency_id, status in dependency_statuses.items()
                if _unit_status_blocks_dependents(status)
            ]
            if failed_dependencies:
                unit_results_by_id[unit.unit_id] = {
                    "unit_id": unit.unit_id,
                    "label": unit.label,
                    "parallel_safe": unit.parallel_safe,
                    "status": "skipped_failed_dependency",
                    "failed_dependencies": failed_dependencies,
                    "depends_on": list(unit.depends_on),
                    **publication_work_unit_lifecycle.instant_timing(clock=_clock_snapshot),
                }
                execution_summary["skipped_dependency_unit_count"] += 1
                continue
            unresolved_dependencies = [
                dependency_id for dependency_id in unit.depends_on if dependency_id not in unit_results_by_id
            ]
            if unresolved_dependencies:
                remaining_units.append(unit)
                continue
            if unit.parallel_safe:
                ready_parallel_units.append(unit)
            else:
                ready_sequential_units.append(unit)
        if not ready_parallel_units and not ready_sequential_units:
            if not remaining_units:
                break
            raise RuntimeError("gate-clearing batch repair dependency graph could not be resolved")
        if ready_parallel_units:
            execution_summary["parallel_wave_count"] += 1
            execution_summary["parallel_unit_count"] += len(ready_parallel_units)
            with ThreadPoolExecutor(max_workers=len(ready_parallel_units)) as executor:
                futures = {
                    unit.unit_id: executor.submit(
                        _run_repair_unit,
                        unit=unit,
                        latest_batch=latest_batch,
                        paper_root=paper_root,
                        gate_report=gate_report,
                        profile=profile,
                    )
                    for unit in ready_parallel_units
                }
                for unit in ready_parallel_units:
                    item, unit_fingerprint = futures[unit.unit_id].result()
                    unit_results_by_id[unit.unit_id] = item
                    if unit_fingerprint is not None:
                        unit_fingerprints[unit.unit_id] = unit_fingerprint
        for unit in ready_sequential_units:
            item, unit_fingerprint = _run_repair_unit(
                unit=unit,
                latest_batch=latest_batch,
                paper_root=paper_root,
                gate_report=gate_report,
                profile=profile,
            )
            unit_results_by_id[unit.unit_id] = item
            if unit_fingerprint is not None:
                unit_fingerprints[unit.unit_id] = unit_fingerprint
            execution_summary["sequential_unit_count"] += 1
        pending_units = remaining_units
    unit_results = [
        unit_results_by_id[unit.unit_id]
        for unit in repair_units
        if unit.unit_id in unit_results_by_id
    ]
    return unit_results, unit_fingerprints, execution_summary


def _reuse_embedded_submission_delivery_sync(
    *,
    create_submission_result: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not isinstance(create_submission_result, dict):
        return None
    delivery_sync = create_submission_result.get("delivery_sync")
    if not isinstance(delivery_sync, dict) or not delivery_sync:
        return None
    return {
        "unit_id": "sync_submission_minimal_delivery",
        "label": "Refresh the study-owned submission-minimal delivery mirror before gate replay",
        "parallel_safe": False,
        "status": _non_empty_text(delivery_sync.get("status")) or "updated",
        "result": delivery_sync,
        "reused_embedded_delivery_sync": True,
        "depends_on": ["create_submission_minimal_package"],
    }


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
    publication_work_unit_payload = publication_work_units.derive_publication_work_units(gate_report)
    if publication_work_unit_payload.get("actionability_status") == "blocked_by_non_actionable_gate":
        return None
    current_required_action = str(gate_report.get("current_required_action") or "").strip()

    medical_surface_blockers = medical_surface_repair_blockers(gate_report)
    repairable_surface = bool(
        medical_surface_blockers & REPAIRABLE_MEDICAL_SURFACE_BLOCKERS
        or "claim_evidence_consistency_failed" in medical_surface_blockers
    )
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
    if (repairable_surface or anchor_repairable) and bounded_analysis_action is None:
        return None

    latest_batch = _latest_batch_record(study_root=study_root)
    current_eval_id = str(publication_eval_payload.get("eval_id") or "").strip()
    if str(latest_batch.get("source_eval_id") or "").strip() == current_eval_id:
        return None

    if anchor_repairable or repairable_surface:
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
    return _parse_json_object_from_cli_stdout(completed.stdout or "")


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


def _sync_submission_minimal_delivery(*, paper_root: Path, profile: WorkspaceProfile) -> dict[str, Any]:
    return study_delivery_sync.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
        publication_profile=profile.default_publication_profile,
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

    explicit_next_work_unit = explicit_next_publication_work_unit(publication_eval_payload)
    selected_publication_work_unit = explicit_next_work_unit or derived_next_publication_work_unit(gate_report)
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
            repair_units.append(
                GateClearingRepairUnit(
                    unit_id="materialize_display_surface",
                    label="Refresh display catalogs and generated paper-facing exports",
                    parallel_safe=True,
                    depends_on=_existing_dependency_ids(repair_units, "repair_paper_live_paths"),
                    run=lambda: _materialize_display_surface(paper_root=paper_root),
                )
            )
    elif bundle_stage_repair and display_repair_script_path.exists():
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
                    sync_submission_minimal_delivery=_sync_submission_minimal_delivery,
                    path_fingerprints=_path_fingerprints,
                    settle_window_ns=CURRENT_PACKAGE_AUTHORITY_SETTLE_WINDOW_NS,
                ),
            )
        )
    if bundle_stage_repair and submission_minimal_refresh_requested:
        repair_units.append(
            GateClearingRepairUnit(
                unit_id="create_submission_minimal_package",
                label="Regenerate submission-minimal assets before gate replay",
                parallel_safe=False,
                depends_on=_existing_dependency_ids(
                    repair_units,
                    "repair_paper_live_paths",
                    "workspace_display_repair_script",
                    "materialize_display_surface",
                ),
                run=lambda: _create_submission_minimal_package(paper_root=paper_root, profile=profile),
            )
        )
    repair_units = filter_repair_units_for_publication_work_unit(
        repair_units,
        next_work_unit=explicit_next_work_unit,
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
    create_submission_unit_result = next(
        (
            item
            for item in unit_results
            if _non_empty_text(item.get("unit_id")) == "create_submission_minimal_package"
        ),
        None,
    )
    submission_minimal_refreshed = create_submission_unit_result is not None and not _unit_status_blocks_dependents(
        _non_empty_text(create_submission_unit_result.get("status"))
    )
    if submission_minimal_refreshed and study_delivery_status.startswith("stale"):
        embedded_delivery_sync = _reuse_embedded_submission_delivery_sync(
            create_submission_result=create_submission_unit_result.get("result")
            if isinstance(create_submission_unit_result, dict)
            else None,
        )
        if embedded_delivery_sync is not None:
            authority_settled, authority_fingerprints = gate_clearing_batch_submission.current_package_authority_settled(
                paper_root=paper_root,
                path_fingerprints=_path_fingerprints,
                settle_window_ns=CURRENT_PACKAGE_AUTHORITY_SETTLE_WINDOW_NS,
            )
            if authority_settled:
                embedded_delivery_sync["authority_fingerprints"] = authority_fingerprints
                embedded_delivery_sync["settle_window_ns"] = CURRENT_PACKAGE_AUTHORITY_SETTLE_WINDOW_NS
                embedded_delivery_sync.update(
                    publication_work_unit_lifecycle.instant_timing(clock=_clock_snapshot)
                )
                unit_results.append(embedded_delivery_sync)
            else:
                retry_metadata = gate_clearing_batch_submission.authority_not_settled_retry_metadata(
                    authority_fingerprints=authority_fingerprints,
                    settle_window_ns=CURRENT_PACKAGE_AUTHORITY_SETTLE_WINDOW_NS,
                )
                unit_results.append(
                    publication_work_unit_lifecycle.authority_not_settled_sync_unit_item(
                        authority_fingerprints=authority_fingerprints,
                        settle_window_ns=CURRENT_PACKAGE_AUTHORITY_SETTLE_WINDOW_NS,
                        retry_metadata=retry_metadata,
                        timing=publication_work_unit_lifecycle.instant_timing(clock=_clock_snapshot),
                        depends_on=["create_submission_minimal_package"],
                    )
                )
            execution_summary["sequential_unit_count"] += 1
        else:
            started_ns, started_at = _clock_snapshot()
            try:
                result = gate_clearing_batch_submission.sync_submission_minimal_delivery_after_settle(
                    paper_root=paper_root,
                    profile=profile,
                    sync_submission_minimal_delivery=_sync_submission_minimal_delivery,
                    path_fingerprints=_path_fingerprints,
                    settle_window_ns=CURRENT_PACKAGE_AUTHORITY_SETTLE_WINDOW_NS,
                )
                finished_ns, finished_at = _clock_snapshot()
                timing = {
                    "started_at": started_at,
                    "finished_at": finished_at,
                    "duration_seconds": publication_work_unit_lifecycle.duration_seconds(started_ns, finished_ns),
                }
                unit_results.append(
                    publication_work_unit_lifecycle.submission_delivery_sync_unit_item(
                        result=result,
                        timing=timing,
                        depends_on=["create_submission_minimal_package"],
                    )
                )
                execution_summary["sequential_unit_count"] += 1
            except Exception as exc:
                finished_ns, finished_at = _clock_snapshot()
                unit_results.append(
                    {
                        "unit_id": "sync_submission_minimal_delivery",
                        "label": "Refresh the study-owned submission-minimal delivery mirror before gate replay",
                        "parallel_safe": False,
                        "status": "failed",
                        "error": str(exc),
                        "depends_on": ["create_submission_minimal_package"],
                        "started_at": started_at,
                        "finished_at": finished_at,
                        "duration_seconds": publication_work_unit_lifecycle.duration_seconds(started_ns, finished_ns),
                    }
                )
                execution_summary["sequential_unit_count"] += 1

    gate_replay, gate_replay_timing = publication_work_unit_lifecycle.timed_step(
        clock=_clock_snapshot,
        run=lambda: publication_gate.run_controller(
            quest_root=quest_root,
            apply=True,
            source=source,
            enqueue_intervention=False,
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
        unit_results=unit_results,
        clock=_clock_snapshot,
        schema_version=SCHEMA_VERSION,
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
        "selected_publication_work_unit": selected_publication_work_unit,
        "explicit_publication_work_unit": explicit_next_work_unit,
        "unit_results": unit_results,
        "unit_fingerprints": unit_fingerprints,
        "repair_unit_execution_plan": repair_unit_execution_plan,
        "execution_summary": execution_summary,
        "gate_replay": gate_replay,
        "gate_replay_step": gate_replay_step,
        "publication_work_unit_lifecycle": lifecycle_record,
    }
    if current_package_freshness_proof is not None:
        record["current_package_freshness_proof"] = current_package_freshness_proof
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
