from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.owner_route_reconcile_parts import study_identity
from med_autoscience.profiles import WorkspaceProfile, load_profile


SURFACE_KIND = "paper_clean_room_rebuild"
REBUILD_ROOT_RELPATH = Path("artifacts") / "stage_outputs" / "_paper_clean_room_rebuild"
SUPERVISION_ROOT_RELPATH = Path("artifacts") / "supervision" / "paper_clean_room_rebuild"
REQUIRED_INPUTS = (
    ("study_yaml", Path("study.yaml")),
    ("current_manuscript", Path("paper/draft.md")),
    ("evidence_ledger", Path("paper/evidence_ledger.json")),
    ("review_ledger", Path("paper/review/review_ledger.json")),
)
OPTIONAL_STUDY_INPUTS = (
    ("claim_evidence_map", Path("paper/claim_evidence_map.json")),
    ("figure_catalog", Path("paper/figures/figure_catalog.json")),
    ("table_catalog", Path("paper/tables/table_catalog.json")),
    ("publication_eval_latest", Path("artifacts/publication_eval/latest.json")),
    ("controller_decision_latest", Path("artifacts/controller_decisions/latest.json")),
    ("paper_authority_cutover", Path("artifacts/stage_outputs/_body_authority/paper_authority_cutover/latest.json")),
)
NEXT_REQUIRED_ACTIONS = [
    "run_medical_publication_surface_from_clean_room",
    "publishability_gate_replay",
    "route_to_write_review_or_finalize_owner",
    "promote_only_after_publication_gate_passes",
]
AUTHORITY_BOUNDARY = {
    "paper_body_mutation_allowed": False,
    "publication_eval_write_allowed": False,
    "controller_decision_write_allowed": False,
    "current_package_write_allowed": False,
    "submission_package_regenerated": False,
    "promote_to_current_authority_allowed": False,
    "old_runtime_residue_import_allowed": False,
}
LEGACY_RESIDUE_POLICY = {
    "legacy_runtime_or_ds_residue_imported": False,
    "legacy_control_surface_imported": False,
    "legacy_run_logs_imported": False,
    "legacy_surfaces_role": "provenance_only",
    "allowed_input_policy": "verified_refs_only",
}


def run_paper_clean_room_rebuild(
    *,
    profile_path: Path,
    study_ids: Iterable[str] | None = None,
    apply: bool,
) -> dict[str, Any]:
    resolved_profile_path = Path(profile_path).expanduser().resolve()
    profile = load_profile(resolved_profile_path)
    selected_study_ids = _resolve_study_ids(profile=profile, study_ids=study_ids)
    recorded_at = _utc_now()
    studies = [
        materialize_paper_clean_room_rebuild(
            profile=profile,
            study_id=study_id,
            recorded_at=recorded_at,
            apply=apply,
        )
        for study_id in selected_study_ids
    ]
    return {
        "schema_version": 1,
        "surface_kind": SURFACE_KIND,
        "mode": "apply" if apply else "dry_run",
        "recorded_at": recorded_at,
        "profile_path": str(resolved_profile_path),
        "workspace_root": str(profile.workspace_root.expanduser().resolve()),
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
        "legacy_residue_policy": dict(LEGACY_RESIDUE_POLICY),
        "study_count": len(studies),
        "studies": studies,
    }


def materialize_paper_clean_room_rebuild(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    recorded_at: str | None = None,
    apply: bool,
) -> dict[str, Any]:
    timestamp = _text(recorded_at) or _utc_now()
    study_root = (profile.studies_root / study_id).expanduser().resolve()
    clean_root = study_root / REBUILD_ROOT_RELPATH / "workspaces" / _history_stamp(timestamp)
    descriptor_path = study_root / SUPERVISION_ROOT_RELPATH / "latest.json"
    history_path = study_root / SUPERVISION_ROOT_RELPATH / "history" / f"{_history_stamp(timestamp)}.json"
    refs = _verified_input_refs(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        clean_root=clean_root,
    )
    missing_required = [
        ref["surface_id"]
        for ref in refs
        if ref["required"] is True and ref["present"] is not True
    ]
    descriptor = _descriptor(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        clean_root=clean_root,
        descriptor_path=descriptor_path,
        history_path=history_path,
        recorded_at=timestamp,
        refs=refs,
        missing_required=missing_required,
    )
    if apply:
        _materialize_verified_inputs(clean_root=clean_root, refs=refs)
        _write_json(history_path, descriptor)
        _write_json(descriptor_path, descriptor)
    return {
        "study_id": study_id,
        "study_root": str(study_root),
        "status": descriptor["status"],
        "clean_workspace_root": str(clean_root),
        "descriptor_path": str(descriptor_path),
        "history_path": str(history_path),
        "verified_input_count": len([ref for ref in refs if ref["present"] is True]),
        "missing_required_refs": missing_required,
        "legacy_residue_policy": dict(LEGACY_RESIDUE_POLICY),
        "next_required_actions": list(NEXT_REQUIRED_ACTIONS),
    }


def _descriptor(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    clean_root: Path,
    descriptor_path: Path,
    history_path: Path,
    recorded_at: str,
    refs: list[dict[str, Any]],
    missing_required: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "surface_kind": SURFACE_KIND,
        "status": "blocked_missing_required_refs" if missing_required else "ready",
        "recorded_at": recorded_at,
        "workspace_root": str(profile.workspace_root.expanduser().resolve()),
        "study_id": study_id,
        "study_root": str(study_root),
        "clean_workspace_root": str(clean_root),
        "descriptor_path": str(descriptor_path),
        "history_path": str(history_path),
        "verified_input_root": str(clean_root / "verified_inputs"),
        "verified_input_refs": refs,
        "missing_required_refs": missing_required,
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
        "legacy_residue_policy": dict(LEGACY_RESIDUE_POLICY),
        "source_selection_policy": {
            "copy_only_verified_current_refs": True,
            "legacy_ds_runtime_state_allowed": False,
            "legacy_dispatch_ledger_allowed": False,
            "stale_read_model_allowed": False,
            "manual_quality_claim_allowed": False,
        },
        "next_required_actions": list(NEXT_REQUIRED_ACTIONS),
    }


def _verified_input_refs(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    clean_root: Path,
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for surface_id, relpath in REQUIRED_INPUTS:
        refs.append(
            _input_ref(
                profile=profile,
                study_root=study_root,
                clean_root=clean_root,
                surface_id=surface_id,
                source_path=study_root / relpath,
                required=True,
            )
        )
    for surface_id, relpath in OPTIONAL_STUDY_INPUTS:
        refs.append(
            _input_ref(
                profile=profile,
                study_root=study_root,
                clean_root=clean_root,
                surface_id=surface_id,
                source_path=study_root / relpath,
                required=False,
            )
        )
    refs.append(
        _input_ref(
            profile=profile,
            study_root=study_root,
            clean_root=clean_root,
            surface_id="publishability_gate_latest",
            source_path=profile.runtime_root / study_id / "artifacts" / "reports" / "publishability_gate" / "latest.json",
            required=False,
        )
    )
    return refs


def _input_ref(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    clean_root: Path,
    surface_id: str,
    source_path: Path,
    required: bool,
) -> dict[str, Any]:
    resolved = source_path.expanduser().resolve()
    present = resolved.exists()
    destination_relpath = _destination_relpath(
        profile=profile,
        study_root=study_root,
        source_path=resolved,
    )
    return {
        "surface_id": surface_id,
        "required": required,
        "present": present,
        "valid": present,
        "source_path": str(resolved),
        "destination_path": str(clean_root / "verified_inputs" / destination_relpath),
        "destination_relative_path": destination_relpath.as_posix(),
        "kind": "directory" if resolved.is_dir() else "file",
        "sha256": _sha256(resolved) if resolved.is_file() else None,
    }


def _destination_relpath(*, profile: WorkspaceProfile, study_root: Path, source_path: Path) -> Path:
    for root in (study_root, profile.workspace_root.expanduser().resolve()):
        try:
            return source_path.relative_to(root)
        except ValueError:
            continue
    return Path("external") / source_path.name


def _materialize_verified_inputs(*, clean_root: Path, refs: list[dict[str, Any]]) -> None:
    verified_root = clean_root / "verified_inputs"
    verified_root.mkdir(parents=True, exist_ok=True)
    for ref in refs:
        if ref["present"] is not True:
            continue
        source = Path(str(ref["source_path"]))
        destination = Path(str(ref["destination_path"]))
        destination.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            if destination.exists():
                continue
            shutil.copytree(source, destination)
        elif not destination.exists():
            shutil.copy2(source, destination)


def _resolve_study_ids(*, profile: WorkspaceProfile, study_ids: Iterable[str] | None) -> tuple[str, ...]:
    selected = tuple(item for raw in (study_ids or ()) if (item := _text(raw)) is not None)
    if selected:
        return selected
    return tuple(study_identity.resolve_owner_route_reconcile_study_ids(profile))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _history_stamp(value: str) -> str:
    return (
        value.replace("-", "")
        .replace(":", "")
        .replace("+", "")
        .replace(".", "")
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "AUTHORITY_BOUNDARY",
    "LEGACY_RESIDUE_POLICY",
    "SURFACE_KIND",
    "materialize_paper_clean_room_rebuild",
    "run_paper_clean_room_rebuild",
]
