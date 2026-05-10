from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.profiles import WorkspaceProfile, load_profile


_FORBIDDEN_PAYLOAD_FLAGS = (
    "domain_truth_write",
    "artifact_gate_override",
    "study_truth_write",
    "publication_quality_verdict",
    "current_package_write",
)
_STUDY_SOURCE_REFS: tuple[tuple[str, Path, str], ...] = (
    ("runtime_supervision_truth", Path("artifacts/runtime/runtime_supervision/latest.json"), "runtime_supervision"),
    ("runtime_supervision_truth_legacy_ref", Path("artifacts/runtime_supervision/latest.json"), "runtime_supervision"),
    ("autonomy_slo_status", Path("artifacts/autonomy/slo_status/latest.json"), "slo_status"),
    ("worker_lease", Path("artifacts/runtime/worker_lease/latest.json"), "worker_lease"),
    ("runtime_session", Path("artifacts/runtime/runtime_session/latest.json"), "runtime_session"),
    ("recovery_intent", Path("artifacts/runtime/recovery_intent/latest.json"), "recovery_intent"),
    ("safe_reconcile_dry_run", Path("artifacts/supervision/reconcile/latest.json"), "safe_reconcile"),
    ("controller_receipt", Path("artifacts/runtime/supervisor_dispatch_receipt/latest.json"), "controller_receipt"),
    ("controller_decisions", Path("artifacts/controller_decisions/latest.json"), "controller_decisions"),
    ("publication_eval", Path("artifacts/publication_eval/latest.json"), "publication_eval"),
)
_ALLOWED_TASK_KINDS = {
    "runtime_supervision/recover": "runtime_supervisor_recover",
    "runtime_supervisor/recover": "runtime_supervisor_recover",
    "runtime/recover": "runtime_supervisor_recover",
    "safe_reconcile/dry-run": "safe_reconcile_dry_run",
    "study_progress/read": "study_progress_read",
    "status/read": "status_read",
    "notification/receipt": "notification_receipt",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return dict(payload) if isinstance(payload, dict) else None


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _workspace_relative(path: Path, *, workspace_root: Path) -> str:
    try:
        return str(path.relative_to(workspace_root))
    except ValueError:
        return str(path)


def _authority_boundary_payload() -> dict[str, Any]:
    return {
        "online_runtime_substrate_owner": "opl_managed_hermes",
        "typed_dispatch_owner": "one-person-lab",
        "domain_truth_owner": "med-autoscience",
        "quality_gate_owner": "med-autoscience",
        "artifact_authority_owner": "med-autoscience",
        "writes_domain_truth": False,
        "writes_artifact_gate": False,
        "forbidden_authorities": [
            "study_truth_write",
            "publication_quality_verdict",
            "artifact_gate_override",
            "current_package_write",
        ],
    }


def _source_ref(*, study_root: Path, role: str, relative_path: Path, workspace_root: Path) -> dict[str, Any]:
    path = study_root / relative_path
    return {
        "ref_kind": "repo_path",
        "role": role,
        "ref": _workspace_relative(path, workspace_root=workspace_root),
        "exists": path.exists(),
    }


def _study_projection(*, study_root: Path, profile: WorkspaceProfile) -> dict[str, Any]:
    source_refs = [
        _source_ref(
            study_root=study_root,
            role=role,
            relative_path=relative_path,
            workspace_root=profile.workspace_root,
        )
        for role, relative_path, _ in _STUDY_SOURCE_REFS
    ]
    payload: dict[str, Any] = {
        "study_id": study_root.name,
        "study_root": str(study_root),
        "domain_owned_source_refs": source_refs,
    }
    for _, relative_path, field_name in _STUDY_SOURCE_REFS:
        if field_name not in payload:
            payload[field_name] = _read_json_object(study_root / relative_path)
    return payload


def _study_roots(profile: WorkspaceProfile) -> list[Path]:
    if not profile.studies_root.is_dir():
        return []
    return sorted(path for path in profile.studies_root.iterdir() if path.is_dir())


def export_family_sidecar(*, profile: WorkspaceProfile, profile_ref: Path) -> dict[str, Any]:
    studies = [_study_projection(study_root=study_root, profile=profile) for study_root in _study_roots(profile)]
    generated_at = _now_iso()
    return {
        "surface_kind": "mas_family_sidecar_export",
        "version": "mas-family-sidecar.v1",
        "target_domain_id": "medautoscience",
        "generated_at": generated_at,
        "profile": {
            "profile_name": profile.name,
            "profile_ref": str(profile_ref),
            "hermes_profile_configured": bool(profile.hermes_agent_repo_root or profile.hermes_home_root),
            "hermes_home_root": str(profile.hermes_home_root),
        },
        "workspace": {
            "workspace_root": str(profile.workspace_root),
            "runtime_root": str(profile.runtime_root),
            "studies_root": str(profile.studies_root),
            "workspace_exists": profile.workspace_root.exists(),
            "studies_root_exists": profile.studies_root.exists(),
        },
        "online_runtime_substrate": {
            "owner": "opl_managed_hermes",
            "provider": "Hermes-Agent",
            "hermes_runtime_provider": "required_for_online_family_runtime",
            "role": "wakeup_session_store_delivery_approval_transport",
            "not_authority_for": ["study_truth", "publication_quality", "artifact_gate", "paper_package"],
        },
        "dispatch": {
            "entrypoint": "medautosci sidecar dispatch --task <task.json> --format json",
            "allowed_task_kinds": sorted(_ALLOWED_TASK_KINDS),
            "receipt_policy": "MAS writes a domain control receipt only; paper, publication, and package truth remain untouched.",
        },
        "authority_boundary": _authority_boundary_payload(),
        "family_runtime_supervision": {
            "surface_kind": "family_runtime_supervision",
            "version": "family-runtime-supervision.v1",
            "target_domain_id": "medautoscience",
            "supervision_id": f"{profile.name}_mas_family_runtime_supervision",
            "adapter_id": "opl_managed_hermes_wakeup_to_mas_sidecar",
            "cadence": {"interval_seconds": 60},
            "lease_freshness": {"state": "unknown", "observed_at": generated_at, "max_age_seconds": 180},
            "slo_state": {
                "state": _aggregate_slo_state(studies),
                "summary": "MAS exposes SLO state as read-only projection for OPL family-runtime indexing.",
            },
            "repair_command": f"medautosci runtime ensure-supervision --profile {profile_ref}",
            "safe_reconcile_hint": "Use medautosci sidecar dispatch; OPL/Hermes must not write study or publication truth.",
            "domain_owned_source_refs": _aggregate_domain_refs(studies),
            "read_only_authority_boundary": {
                "projection_owner": "one-person-lab",
                "runtime_owner": "med-autoscience",
                "scheduler_owner": "med-autoscience",
                "authority": "read_only_projection",
                "forbidden_authorities": _authority_boundary_payload()["forbidden_authorities"],
            },
        },
        "studies": studies,
    }


def _aggregate_slo_state(studies: list[Mapping[str, Any]]) -> str:
    states = {
        _text(_mapping(study.get("slo_status")).get("state"))
        for study in studies
        if _mapping(study.get("slo_status"))
    }
    if "breach" in states:
        return "breach"
    if "watch" in states:
        return "watch"
    if "met" in states:
        return "met"
    return "unknown"


def _aggregate_domain_refs(studies: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for study in studies:
        for ref in study.get("domain_owned_source_refs") or []:
            if isinstance(ref, dict) and ref.get("exists") is True:
                refs.append(ref)
    return refs[:50]


def _load_task(task_path: Path) -> dict[str, Any]:
    payload = _read_json_object(task_path)
    if payload is None:
        raise ValueError(f"sidecar task must be a JSON object: {task_path}")
    return payload


def _forbidden_write_requested(task: Mapping[str, Any]) -> bool:
    payload = _mapping(task.get("payload"))
    if any(bool(payload.get(flag)) for flag in _FORBIDDEN_PAYLOAD_FLAGS):
        return True
    requested_writes = payload.get("requested_writes")
    if isinstance(requested_writes, list):
        forbidden = {"study_truth", "publication_eval", "controller_decisions", "current_package", "artifact_gate"}
        return any(str(item) in forbidden for item in requested_writes)
    return False


def _profile_from_task(task: Mapping[str, Any]) -> tuple[WorkspaceProfile | None, Path | None]:
    payload = _mapping(task.get("payload"))
    profile_ref = _text(payload.get("profile") or payload.get("profile_path"))
    if profile_ref is None:
        return None, None
    path = Path(profile_ref).expanduser()
    return load_profile(path), path


def _receipt_path(*, profile: WorkspaceProfile, task_id: str) -> Path:
    digest = hashlib.sha256(task_id.encode("utf-8")).hexdigest()[:20]
    return profile.workspace_root / "artifacts" / "runtime" / "opl_family_sidecar" / "dispatch_receipts" / f"{digest}.json"


def _recommended_command(action_type: str, *, profile_ref: Path | None, study_id: str | None) -> str:
    profile_part = f" --profile {profile_ref}" if profile_ref is not None else " --profile <profile>"
    study_part = f" --studies {study_id}" if study_id else ""
    if action_type == "runtime_supervisor_recover":
        return f"uv run python -m med_autoscience.cli runtime-supervisor-scan{profile_part}{study_part}"
    if action_type == "safe_reconcile_dry_run":
        return f"uv run python -m med_autoscience.cli runtime-supervisor-reconcile{profile_part}{study_part} --mode developer_apply_safe --dry-run"
    if action_type == "study_progress_read":
        return f"uv run python -m med_autoscience.cli study-progress{profile_part}{study_part} --format json"
    return f"uv run python -m med_autoscience.cli product-entry-status{profile_part} --format json"


def dispatch_family_sidecar_task(*, task_path: Path) -> dict[str, Any]:
    generated_at = _now_iso()
    try:
        task = _load_task(task_path)
    except ValueError as exc:
        return _dispatch_error(generated_at=generated_at, reason="invalid_task", detail=str(exc))
    task_id = _text(task.get("task_id")) or "unknown_task"
    domain_id = _text(task.get("domain_id")) or "medautoscience"
    task_kind = _text(task.get("task_kind")) or "unknown"
    if domain_id != "medautoscience":
        return _dispatch_error(
            generated_at=generated_at,
            task_id=task_id,
            reason="wrong_domain",
            detail=f"MAS sidecar cannot dispatch domain {domain_id}",
        )
    if _forbidden_write_requested(task):
        return _dispatch_error(
            generated_at=generated_at,
            task_id=task_id,
            task_kind=task_kind,
            reason="domain_truth_or_artifact_gate_write_forbidden",
            forbidden_domain_truth_write=True,
        )
    action_type = _ALLOWED_TASK_KINDS.get(task_kind)
    if action_type is None:
        return _dispatch_error(
            generated_at=generated_at,
            task_id=task_id,
            task_kind=task_kind,
            reason="unsupported_task_kind",
            detail=f"Unsupported MAS sidecar task kind: {task_kind}",
        )
    profile, profile_ref = _profile_from_task(task)
    study_id = _text(_mapping(task.get("payload")).get("study_id"))
    receipt = {
        "surface_kind": "mas_family_sidecar_dispatch_receipt",
        "version": "mas-family-sidecar.v1",
        "accepted": True,
        "task_id": task_id,
        "task_kind": task_kind,
        "generated_at": generated_at,
        "source_task_ref": str(task_path),
        "will_start_llm_worker": False,
        "dispatch": {
            "action_type": action_type,
            "study_id": study_id,
            "recommended_domain_command": _recommended_command(action_type, profile_ref=profile_ref, study_id=study_id),
            "execution_policy": "guarded_domain_control_receipt_only",
        },
        "authority_boundary": _authority_boundary_payload(),
    }
    if profile is not None:
        path = _receipt_path(profile=profile, task_id=task_id)
        if path.exists():
            existing = _read_json_object(path)
            if existing is not None:
                existing["idempotent_noop"] = True
                return existing
        receipt["receipt_ref"] = _workspace_relative(path, workspace_root=profile.workspace_root)
        _write_json(path, receipt)
    return receipt


def _dispatch_error(
    *,
    generated_at: str,
    reason: str,
    task_id: str | None = None,
    task_kind: str | None = None,
    detail: str | None = None,
    forbidden_domain_truth_write: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "surface_kind": "mas_family_sidecar_dispatch_receipt",
        "version": "mas-family-sidecar.v1",
        "accepted": False,
        "generated_at": generated_at,
        "reason": reason,
        "forbidden_domain_truth_write": forbidden_domain_truth_write,
        "authority_boundary": _authority_boundary_payload(),
    }
    if task_id is not None:
        payload["task_id"] = task_id
    if task_kind is not None:
        payload["task_kind"] = task_kind
    if detail is not None:
        payload["detail"] = detail
    return payload
