from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile, load_profile, profile_to_dict


SURFACE = "real_paper_autonomy_soak_inventory"
SCHEMA_VERSION = 1
DEFAULT_PROFILE_GLOB = "*/ops/medautoscience/profiles/*.toml"
DEFAULT_YANG_ROOT = Path("/Users/gaofeng/workspace/Yang")

READ_ONLY_CONTRACT = {
    "mode": "dry_run_inventory",
    "writes_real_workspace": False,
    "can_mutate_runtime": False,
    "can_write_current_package": False,
    "can_write_publication_gate": False,
    "allowed_actions": ["read_profiles", "read_status_surfaces", "report_inventory"],
    "prohibited_actions": [
        "migration_apply",
        "reconcile_apply",
        "runtime_relaunch",
        "current_package_write",
        "publication_gate_write",
    ],
}
SOAK_PROJECTION_SURFACE = "real_paper_autonomy_soak_projection"
SOAK_ACCEPTED_STATES = (
    "artifact_delta",
    "gate_replay",
    "ai_reviewer_re_eval",
    "route_decision",
    "stop_loss",
    "human_gate",
    "stable_blocker",
    "continuing_repair",
    "unknown",
)

STATUS_SURFACE_REFS: tuple[str, ...] = (
    "artifacts/runtime/runtime_status_summary.json",
    "artifacts/runtime/runtime_supervision/latest.json",
    "artifacts/runtime/study_macro_state/latest.json",
    "artifacts/truth/latest.json",
    "artifacts/controller_decisions/latest.json",
    "artifacts/publication_eval/latest.json",
)

LEGACY_MDS_LAUNCHER_REFS: tuple[str, ...] = (
    "ops/med-deepscientist",
    "ops/medautoscience/bin/watch-runtime",
    "ops/medautoscience/bin/install-watch-runtime-service",
)


def discover_yang_profile_paths(
    yang_root: str | Path = DEFAULT_YANG_ROOT,
    *,
    profile_glob: str = DEFAULT_PROFILE_GLOB,
) -> list[Path]:
    root = Path(yang_root).expanduser()
    if not root.exists():
        return []
    return sorted(path.resolve() for path in root.glob(profile_glob) if path.is_file())


def build_real_paper_autonomy_soak_inventory(
    *,
    yang_root: str | Path = DEFAULT_YANG_ROOT,
    profile_paths: Sequence[str | Path] | None = None,
) -> dict[str, Any]:
    paths = [Path(path).expanduser().resolve() for path in profile_paths] if profile_paths else discover_yang_profile_paths(yang_root)
    reports = [_profile_report(path) for path in paths]
    status_counts: dict[str, int] = {}
    for report in reports:
        readiness = _text(report.get("migration_readiness"))
        status_counts[readiness] = status_counts.get(readiness, 0) + 1
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "mode": "dry_run_inventory",
        "read_only_contract": dict(READ_ONLY_CONTRACT),
        "profile_glob": str(Path(yang_root).expanduser() / DEFAULT_PROFILE_GLOB),
        "profile_count": len(reports),
        "profiles": reports,
        "summary": {
            "profiles_discovered": len(reports),
            "migration_readiness_counts": status_counts,
            "writes_performed": False,
            "real_workspace_mutation_allowed": False,
        },
    }


def build_real_paper_autonomy_soak_projection(
    *,
    yang_root: str | Path = DEFAULT_YANG_ROOT,
    profile_paths: Sequence[str | Path] | None = None,
    target_studies: Sequence[str] = ("DM002", "DM003", "Obesity"),
) -> dict[str, Any]:
    paths = [Path(path).expanduser().resolve() for path in profile_paths] if profile_paths else discover_yang_profile_paths(yang_root)
    targets = tuple(target_studies)
    profiles = [_profile_soak_projection(path, target_studies=targets) for path in paths]
    state_counts = {state: 0 for state in SOAK_ACCEPTED_STATES}
    for profile in profiles:
        for study in profile.get("studies", []):
            state = _text(_mapping(study).get("final_projection")) or "unknown"
            state_counts[state] = state_counts.get(state, 0) + 1
    return {
        "surface": SOAK_PROJECTION_SURFACE,
        "schema_version": SCHEMA_VERSION,
        "mode": "read_only_soak_projection",
        "read_only_contract": dict(READ_ONLY_CONTRACT, mode="read_only_soak_projection"),
        "profile_count": len(profiles),
        "profiles": profiles,
        "summary": {
            "target_studies": list(targets),
            "accepted_state_counts": state_counts,
            "writes_performed": False,
            "real_workspace_mutation_allowed": False,
        },
    }


def _profile_soak_projection(profile_path: Path, *, target_studies: Sequence[str]) -> dict[str, Any]:
    base: dict[str, Any] = {
        "profile_path": str(profile_path),
        "profile_readable": False,
        "profile_error": "",
        "studies": [],
    }
    try:
        profile = load_profile(profile_path)
    except Exception as exc:  # pragma: no cover - exact parser errors are reported, not normalized.
        base["profile_error"] = f"{type(exc).__name__}: {exc}"
        return base
    target_set = {str(study_id).strip() for study_id in target_studies if str(study_id).strip()}
    studies = [
        _study_soak_projection(study_root)
        for study_root in _study_roots(profile)
        if not target_set or _matches_target_study(study_root.name, target_set)
    ]
    base.update(
        {
            "profile_readable": True,
            "profile_name": profile.name,
            "workspace_root": str(profile.workspace_root),
            "studies": studies,
        }
    )
    return base


def _matches_target_study(study_id: str, target_studies: set[str]) -> bool:
    normalized = _normalize_study_id(study_id)
    return any(normalized == _normalize_study_id(target) for target in target_studies)


def _normalize_study_id(study_id: str) -> str:
    text = str(study_id or "").strip().lower().replace("_", "-")
    aliases = {
        "dm002": "002",
        "dm-002": "002",
        "dm003": "003",
        "dm-003": "003",
        "obesity": "obesity",
    }
    if text in aliases:
        return aliases[text]
    if text.startswith("002-"):
        return "002"
    if text.startswith("003-"):
        return "003"
    if "obesity" in text:
        return "obesity"
    return text


def _study_soak_projection(study_root: Path) -> dict[str, Any]:
    surfaces = {
        "sidecar_task": _latest_json_from_candidates(
            study_root / "artifacts" / "runtime" / "opl_family_sidecar",
            patterns=("exported_task.json", "*task*.json"),
        ),
        "dispatch_receipt": _latest_json_from_candidates(
            study_root / "artifacts" / "runtime" / "opl_family_sidecar" / "dispatch_receipts",
            patterns=("latest.json", "*.json"),
        ),
        "repair_execution_receipt": _read_json_mapping(
            study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json"
        ),
        "repair_execution_evidence": _read_json_mapping(
            study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
        ),
        "gate_replay": _read_json_mapping(study_root / "artifacts" / "controller" / "gate_replay_requests" / "latest.json"),
        "controller_decisions": _read_json_mapping(study_root / "artifacts" / "controller_decisions" / "latest.json"),
        "publication_eval": _read_json_mapping(study_root / "artifacts" / "publication_eval" / "latest.json"),
        "ai_reviewer_request": _read_json_mapping(
            study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
        ),
    }
    lifecycle = _study_lifecycle([payload for payload in surfaces.values() if isinstance(payload, Mapping)])
    final_projection = _final_projection(surfaces)
    return {
        "study_id": study_root.name,
        "study_root": str(study_root),
        "status": lifecycle["status"],
        "reason": lifecycle["reason"],
        "active_run_id": lifecycle["active_run_id"],
        "final_projection": final_projection,
        "next_owner": _next_owner(surfaces),
        "source_refs": _soak_source_refs(study_root),
        **surfaces,
        "ai_reviewer_evidence": _ai_reviewer_evidence(surfaces["publication_eval"], surfaces["ai_reviewer_request"]),
    }


def _final_projection(surfaces: Mapping[str, Mapping[str, Any]]) -> str:
    repair_evidence = _mapping(surfaces.get("repair_execution_evidence"))
    if _mapping(repair_evidence.get("canonical_artifact_delta")).get("meaningful_artifact_delta") is True:
        return "artifact_delta"
    if repair_evidence.get("progress_delta_candidate") is True:
        return "artifact_delta"
    if _mapping(surfaces.get("publication_eval")).get("assessment_provenance"):
        return "ai_reviewer_re_eval"
    if _mapping(surfaces.get("gate_replay")):
        return "gate_replay"
    controller = _mapping(surfaces.get("controller_decisions"))
    if _text(controller.get("route_decision")):
        if _text(controller.get("route_decision")) in {"stop_loss", "terminal_stop"} or _text(controller.get("route_target")) == "stop":
            return "stop_loss"
        if controller.get("requires_human_confirmation") is True:
            return "human_gate"
        return "route_decision"
    if _mapping(surfaces.get("dispatch_receipt")).get("accepted") is False:
        return "stable_blocker"
    if _mapping(surfaces.get("sidecar_task")):
        return "continuing_repair"
    return "unknown"


def _next_owner(surfaces: Mapping[str, Mapping[str, Any]]) -> str | None:
    repair_receipt = _mapping(surfaces.get("repair_execution_receipt"))
    if repair_receipt.get("execution_status") == "executed":
        return "ai_reviewer"
    task = _mapping(surfaces.get("sidecar_task"))
    payload = _mapping(task.get("payload"))
    unit = _mapping(payload.get("repair_work_unit"))
    if owner := _text(unit.get("owner")):
        return owner
    controller = _mapping(surfaces.get("controller_decisions"))
    return _text(controller.get("next_owner") or controller.get("route_target"))


def _ai_reviewer_evidence(publication_eval: Mapping[str, Any], ai_reviewer_request: Mapping[str, Any]) -> dict[str, Any]:
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    return {
        "owner": _text(provenance.get("owner")) or None,
        "eval_id": _text(publication_eval.get("eval_id")) or None,
        "request_id": _text(ai_reviewer_request.get("request_id")) or None,
        "request_state": _text(_mapping(ai_reviewer_request.get("request_lifecycle")).get("state")) or None,
    }


def _soak_source_refs(study_root: Path) -> list[dict[str, Any]]:
    refs = []
    for relative_ref in (
        "artifacts/runtime/opl_family_sidecar",
        "artifacts/controller/repair_execution_receipts/latest.json",
        "artifacts/controller/repair_execution_evidence/latest.json",
        "artifacts/publication_eval/latest.json",
        "artifacts/controller_decisions/latest.json",
    ):
        path = study_root / relative_ref
        refs.append({"relative_ref": relative_ref, "path": str(path), "exists": path.exists()})
    return refs


def _latest_json_from_candidates(root: Path, *, patterns: Sequence[str]) -> dict[str, Any]:
    if not root.exists():
        return {}
    candidates: list[Path] = []
    for pattern in patterns:
        candidates.extend(path for path in root.glob(pattern) if path.is_file())
    if not candidates:
        return {}
    path = sorted(candidates, key=lambda item: item.stat().st_mtime_ns, reverse=True)[0]
    payload = _read_json_mapping(path)
    return {**dict(payload), "source_ref": str(path)} if payload else {}


def _profile_report(profile_path: Path) -> dict[str, Any]:
    base: dict[str, Any] = {
        "profile_path": str(profile_path),
        "profile_readable": False,
        "profile_error": "",
        "migration_readiness": "profile_unreadable",
        "studies": [],
        "legacy_mds_evidence": [],
    }
    try:
        profile = load_profile(profile_path)
    except Exception as exc:  # pragma: no cover - exact parser errors are reported, not normalized.
        base["profile_error"] = f"{type(exc).__name__}: {exc}"
        return base

    profile_dict = profile_to_dict(profile)
    studies = [_study_report(study_root) for study_root in _study_roots(profile)]
    legacy_evidence = _legacy_mds_evidence(profile=profile, profile_dict=profile_dict)
    readiness = _migration_readiness(
        profile=profile,
        studies=studies,
        legacy_evidence=legacy_evidence,
    )
    base.update(
        {
            "profile_readable": True,
            "profile_name": profile.name,
            "workspace_root": str(profile.workspace_root),
            "runtime_root": str(profile.runtime_root),
            "managed_runtime_home": str(profile.managed_runtime_home),
            "studies_root": str(profile.studies_root),
            "migration_readiness": readiness,
            "status_progress_readability": _status_progress_readability(studies),
            "studies": studies,
            "legacy_mds_evidence": legacy_evidence,
        }
    )
    return base


def _study_roots(profile: WorkspaceProfile) -> list[Path]:
    if not profile.studies_root.is_dir():
        return []
    return sorted(path.resolve() for path in profile.studies_root.iterdir() if path.is_dir())


def _study_report(study_root: Path) -> dict[str, Any]:
    surfaces = [_surface_report(study_root, relative_ref) for relative_ref in STATUS_SURFACE_REFS]
    readable = [surface for surface in surfaces if surface["readable"]]
    status_payloads = [surface["payload"] for surface in readable if isinstance(surface.get("payload"), Mapping)]
    lifecycle = _study_lifecycle(status_payloads)
    return {
        "study_id": _study_id(study_root, status_payloads),
        "study_root": str(study_root),
        "status": lifecycle["status"],
        "reason": lifecycle["reason"],
        "active_run_id": lifecycle["active_run_id"],
        "status_progress_readable": bool(readable),
        "readable_surface_count": len(readable),
        "surface_refs": [
            {
                "relative_ref": surface["relative_ref"],
                "path": surface["path"],
                "exists": surface["exists"],
                "readable": surface["readable"],
                "error": surface["error"],
            }
            for surface in surfaces
        ],
    }


def _surface_report(study_root: Path, relative_ref: str) -> dict[str, Any]:
    path = study_root / relative_ref
    report: dict[str, Any] = {
        "relative_ref": relative_ref,
        "path": str(path),
        "exists": path.is_file(),
        "readable": False,
        "error": "",
        "payload": {},
    }
    if not path.is_file():
        return report
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        return report
    report["readable"] = isinstance(payload, Mapping)
    report["payload"] = dict(payload) if isinstance(payload, Mapping) else {}
    if not report["readable"]:
        report["error"] = "json payload is not an object"
    return report


def _read_json_mapping(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _study_lifecycle(payloads: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    active_run_id = _first_text(payloads, "active_run_id")
    quest_status = _first_text(payloads, "quest_status", "runtime_status", "health_status", "overall_status")
    reason = _first_text(
        payloads,
        "runtime_reason",
        "reason",
        "blocked_reason",
        "status_summary",
        "next_action_summary",
    )
    if active_run_id:
        status = "active"
    elif any(_truthy_nested(payload, ("auto_runtime_parked", "parked")) for payload in payloads):
        status = "parked"
        reason = reason or "auto_runtime_parked"
    elif quest_status in {"completed", "done", "complete"}:
        status = "completed"
    elif quest_status in {"inactive", "blocked", "stopped", "paused", "parked"}:
        status = "parked" if "park" in reason or quest_status == "parked" else "inactive"
    elif payloads:
        status = "readable_unknown"
    else:
        status = "status_unreadable"
        reason = "no readable status/progress surface found"
    return {
        "status": status,
        "reason": reason,
        "active_run_id": active_run_id,
    }


def _study_id(study_root: Path, payloads: Sequence[Mapping[str, Any]]) -> str:
    return _first_text(payloads, "study_id") or study_root.name


def _status_progress_readability(studies: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    readable = [study for study in studies if study.get("status_progress_readable") is True]
    return {
        "study_count": len(studies),
        "readable_study_count": len(readable),
        "all_discovered_studies_readable": len(readable) == len(studies) if studies else False,
    }


def _legacy_mds_evidence(
    *,
    profile: WorkspaceProfile,
    profile_dict: Mapping[str, Any],
) -> list[dict[str, str]]:
    evidence: list[dict[str, str]] = []
    for key in ("runtime_root", "managed_runtime_home"):
        value = _text(profile_dict.get(key))
        if "med-deepscientist" in value or "/.ds" in value:
            evidence.append({"kind": "profile_path", "key": key, "value": value})
    for table_name in ("historical_fixture_ref", "source_provenance", "explicit_archive_import_ref"):
        table = profile_dict.get(table_name)
        if isinstance(table, Mapping):
            for key, raw_value in table.items():
                value = _text(raw_value)
                if "med-deepscientist" in value or "/.ds" in value:
                    evidence.append({"kind": table_name, "key": str(key), "value": value})
    for relative_ref in LEGACY_MDS_LAUNCHER_REFS:
        path = profile.workspace_root / relative_ref
        if path.exists():
            evidence.append({"kind": "workspace_path", "key": relative_ref, "value": str(path)})
    return evidence


def _migration_readiness(
    *,
    profile: WorkspaceProfile,
    studies: Sequence[Mapping[str, Any]],
    legacy_evidence: Sequence[Mapping[str, str]],
) -> str:
    if not profile.workspace_root.exists() or not profile.studies_root.exists():
        return "blocked_missing_workspace_surfaces"
    if not studies:
        return "blocked_no_discovered_studies"
    if any(study.get("status") == "active" for study in studies):
        return "audit_only_active_study_present"
    if legacy_evidence:
        return "dry_run_ready_legacy_evidence_present"
    return "dry_run_ready_no_legacy_evidence"


def _first_text(payloads: Sequence[Mapping[str, Any]], *keys: str) -> str:
    for payload in payloads:
        for key in keys:
            value = _text(payload.get(key))
            if value:
                return value
    return ""


def _truthy_nested(payload: Mapping[str, Any], keys: tuple[str, str]) -> bool:
    parent = payload.get(keys[0])
    return isinstance(parent, Mapping) and parent.get(keys[1]) is True


def _text(value: object) -> str:
    return str(value or "").strip()


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
