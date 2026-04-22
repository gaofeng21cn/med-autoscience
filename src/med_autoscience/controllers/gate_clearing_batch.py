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
        "stale_submission_minimal_authority",
        "submission_surface_qc_failure_present",
        "submission_hardening_incomplete",
    }
)
_SUBMISSION_MINIMAL_REPAIR_GATE_BLOCKERS = frozenset(
    {
        "stale_submission_minimal_authority",
        "submission_surface_qc_failure_present",
        "submission_hardening_incomplete",
    }
)
_DIRECT_SUBMISSION_DELIVERY_SYNC_STALE_REASONS = frozenset(
    {
        "delivery_projection_missing",
        "delivery_manifest_source_changed",
        "delivery_manifest_source_mismatch",
    }
)


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


def _path_fingerprint(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        return {"path": str(resolved), "exists": False}
    stat = resolved.stat()
    return {
        "path": str(resolved),
        "exists": True,
        "size": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def _globbed_path_fingerprints(root: Path, *patterns: str, limit: int = 64) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    fingerprints: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if not path.is_file():
                continue
            resolved = path.expanduser().resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            fingerprint = _path_fingerprint(resolved)
            if fingerprint is not None:
                fingerprints.append(fingerprint)
            if len(fingerprints) >= limit:
                return fingerprints
    return fingerprints


def _path_fingerprints(*paths: Path | None, limit: int = 64) -> list[dict[str, Any]]:
    fingerprints: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for path in paths:
        if path is None:
            continue
        resolved = path.expanduser().resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        fingerprint = _path_fingerprint(resolved)
        if fingerprint is not None:
            fingerprints.append(fingerprint)
        if len(fingerprints) >= limit:
            break
    return fingerprints


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
        managed_submission_surface_roots = tuple(
            root.resolve()
            for root in submission_minimal.resolve_managed_submission_surface_roots(paper_root)
            if root.resolve() != submission_root.resolve()
        )
        compiled_pdf_candidate_values = [
            compile_report.get("output_pdf"),
            compile_report.get("pdf_path"),
            bundle_manifest.get("pdf_path"),
        ]
        exclude_live_submission_root = _candidate_values_include_root(
            workspace_root=workspace_root,
            candidate_values=compiled_pdf_candidate_values,
            root=submission_root,
        )
        excluded_compiled_source_roots = managed_submission_surface_roots + (
            (submission_root.resolve(),) if exclude_live_submission_root else ()
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
            "study_delivery_status": _study_delivery_status(gate_report),
            "study_delivery_stale_reason": _study_delivery_stale_reason(gate_report),
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
    return status not in {None, "failed", "missing", "skipped_failed_dependency", "skipped_matching_unit_fingerprint"}


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
    return status in {"failed", "missing", "skipped_failed_dependency"}


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
        }
        if last_success_status is not None:
            item["last_success_status"] = last_success_status
    else:
        try:
            result = unit.run()
            item = {
                "unit_id": unit.unit_id,
                "label": unit.label,
                "parallel_safe": unit.parallel_safe,
                "status": str(result.get("status") or "ok"),
                "result": result,
            }
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
        or "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？"
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


def _study_delivery_status(gate_report: dict[str, Any]) -> str:
    return str(gate_report.get("study_delivery_status") or "").strip()


def _study_delivery_stale_reason(gate_report: dict[str, Any]) -> str:
    return str(gate_report.get("study_delivery_stale_reason") or "").strip()


def _submission_minimal_refresh_requested(*, gate_report: dict[str, Any]) -> bool:
    current_required_action = str(gate_report.get("current_required_action") or "").strip()
    if current_required_action == "complete_bundle_stage":
        return True
    return bool(_gate_blockers(gate_report) & _SUBMISSION_MINIMAL_REPAIR_GATE_BLOCKERS)


def _direct_submission_delivery_sync_requested(*, gate_report: dict[str, Any]) -> bool:
    return (
        _study_delivery_status(gate_report).startswith("stale")
        and _study_delivery_stale_reason(gate_report) in _DIRECT_SUBMISSION_DELIVERY_SYNC_STALE_REASONS
    )


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
    study_delivery_status = _study_delivery_status(gate_report)
    submission_minimal_refresh_requested = _submission_minimal_refresh_requested(gate_report=gate_report)
    direct_submission_delivery_sync_requested = (
        bundle_stage_repair
        and not submission_minimal_refresh_requested
        and _direct_submission_delivery_sync_requested(gate_report=gate_report)
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
                run=lambda: _sync_submission_minimal_delivery(paper_root=paper_root, profile=profile),
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
            unit_results.append(embedded_delivery_sync)
            execution_summary["sequential_unit_count"] += 1
        else:
            try:
                result = _sync_submission_minimal_delivery(paper_root=paper_root, profile=profile)
                unit_results.append(
                    {
                        "unit_id": "sync_submission_minimal_delivery",
                        "label": "Refresh the study-owned submission-minimal delivery mirror before gate replay",
                        "parallel_safe": False,
                        "status": str(result.get("status") or "updated"),
                        "result": result,
                        "depends_on": ["create_submission_minimal_package"],
                    }
                )
                execution_summary["sequential_unit_count"] += 1
            except Exception as exc:
                unit_results.append(
                    {
                        "unit_id": "sync_submission_minimal_delivery",
                        "label": "Refresh the study-owned submission-minimal delivery mirror before gate replay",
                        "parallel_safe": False,
                        "status": "failed",
                        "error": str(exc),
                        "depends_on": ["create_submission_minimal_package"],
                    }
                )
                execution_summary["sequential_unit_count"] += 1

    gate_replay = publication_gate.run_controller(
        quest_root=quest_root,
        apply=True,
        source=source,
        enqueue_intervention=False,
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
        "unit_fingerprints": unit_fingerprints,
        "execution_summary": execution_summary,
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
