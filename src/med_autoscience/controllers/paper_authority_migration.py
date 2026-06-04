from __future__ import annotations

import hashlib
import json
import shutil
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import domain_action_request_lifecycle
from med_autoscience.controllers import domain_action_requests
from med_autoscience.controllers.owner_route_reconcile_parts import study_identity
from med_autoscience.profiles import WorkspaceProfile, load_profile


SURFACE_KIND = "paper_authority_clean_migration"
MIGRATION_ROOT_RELPATH = Path("artifacts") / "stage_outputs" / "_body_authority" / "paper_authority_cutover"
HISTORY_ROOT_RELPATH = MIGRATION_ROOT_RELPATH / "history"
BODY_ROOT_RELPATH = MIGRATION_ROOT_RELPATH / "current_body"
NONCANONICAL_RESIDUE_ROOT_RELPATH = (
    Path("artifacts") / "stage_outputs" / "_body_authority" / "noncanonical_paper_authority_residue"
)
NONCANONICAL_RESIDUE_HISTORY_ROOT_RELPATH = NONCANONICAL_RESIDUE_ROOT_RELPATH / "history"
LEGACY_BODY_SURFACES = (
    ("paper_body_root", Path("paper"), "canonical_body_authority"),
    ("manuscript_body_root", Path("manuscript"), "human_handoff_body_authority"),
)
ACTIVE_SURFACES = (
    ("publication_eval_latest", Path("artifacts/publication_eval/latest.json"), "quality_authority"),
    (
        "ai_reviewer_publication_eval_responses",
        Path("artifacts/publication_eval/ai_reviewer_responses"),
        "quality_authority",
    ),
    ("controller_decision_latest", Path("artifacts/controller_decisions/latest.json"), "controller_authority"),
    (
        "controller_confirmation_latest",
        Path("artifacts/controller/confirmation/latest.json"),
        "controller_authority",
    ),
    (
        "controller_confirmation_summary",
        Path("artifacts/controller_confirmation_summary.json"),
        "controller_authority",
    ),
    (
        "current_package_freshness_latest",
        Path("artifacts/controller/current_package_freshness/latest.json"),
        "artifact_authority",
    ),
    ("gate_clearing_batch_latest", Path("artifacts/controller/gate_clearing_batch/latest.json"), "controller_authority"),
    ("manuscript_delivery_manifest", Path("manuscript/delivery_manifest.json"), "artifact_authority"),
    ("manuscript_submission_manifest", Path("manuscript/submission_manifest.json"), "artifact_authority"),
    ("manuscript_current_package", Path("manuscript/current_package"), "artifact_authority"),
    ("manuscript_current_package_zip", Path("manuscript/current_package.zip"), "artifact_authority"),
)
PAPER_BODY_REF_SURFACES = {
    "manuscript": (
        Path("paper/draft.md"),
        Path("paper/manuscript.md"),
        Path("paper/build/review_manuscript.md"),
    ),
    "evidence_ledger": (Path("paper/evidence_ledger.json"),),
    "review_ledger": (
        Path("paper/review/review_ledger.json"),
        Path("paper/review_ledger.json"),
    ),
    "medical_manuscript_blueprint": (Path("paper/medical_manuscript_blueprint.json"),),
    "claim_evidence_map": (Path("paper/claim_evidence_map.json"),),
    "medical_prose_review": (
        Path("artifacts/publication_eval/medical_prose_review.json"),
        Path("paper/medical_prose_review.json"),
        Path("paper/review/medical_prose_review.json"),
    ),
}


def run_paper_authority_clean_migration(
    *,
    profile_path: Path,
    study_ids: Iterable[str] | None = None,
    apply: bool,
) -> dict[str, Any]:
    resolved_profile_path = Path(profile_path).expanduser().resolve()
    profile = load_profile(resolved_profile_path)
    selected_study_ids = _resolve_study_ids(profile=profile, study_ids=study_ids)
    noncanonical_residue_dirs = _discover_noncanonical_paper_authority_residue_dirs(profile)
    recorded_at = _utc_now()
    studies = [
        _study_plan(
            profile=profile,
            study_id=study_id,
            recorded_at=recorded_at,
        )
        for study_id in selected_study_ids
    ]
    report: dict[str, Any] = {
        "schema_version": 1,
        "surface_kind": SURFACE_KIND,
        "mode": "apply" if apply else "dry_run",
        "recorded_at": recorded_at,
        "profile_path": str(resolved_profile_path),
        "workspace_root": str(profile.workspace_root.expanduser().resolve()),
        "authority_boundary": {
            "legacy_reader_normalization": True,
            "paper_content_mutation": False,
            "canonical_paper_mutation": False,
            "quality_verdict_written": False,
            "submission_package_regenerated": False,
            "active_truth_surfaces_archived": bool(studies),
        },
        "migration_policy": {
            "legacy_artifacts_role_after_cutover": "provenance_only",
            "executable_truth_owner_after_cutover": "new_mas_owner_surfaces",
            "unknown_legacy_schema_policy": "fail_closed_rehydrate_re_evaluate_rebuild",
            "required_next_owner_sequence": [
                "ai_reviewer",
                "publication_gate",
                "artifact_os",
            ],
        },
        "study_count": len(studies),
        "studies": studies,
        "noncanonical_paper_authority_residue_dirs": noncanonical_residue_dirs,
        "next_required_actions": _workspace_next_actions(studies),
    }
    if apply:
        for study in studies:
            if study["cutover_required"]:
                _apply_study_cutover(profile=profile, study_plan=study, recorded_at=recorded_at)
        residue_migrations = _apply_noncanonical_residue_cutover(
            profile=profile,
            residue_dirs=noncanonical_residue_dirs,
            recorded_at=recorded_at,
        )
        report["studies"] = [
            _study_plan(profile=profile, study_id=study_id, recorded_at=recorded_at)
            for study_id in selected_study_ids
        ]
        report["noncanonical_paper_authority_residue_dirs"] = _discover_noncanonical_paper_authority_residue_dirs(
            profile
        )
        report["next_required_actions"] = _workspace_next_actions(report["studies"])
        report["post_apply"] = {
            "active_surface_count": sum(len(study["active_surfaces"]) for study in report["studies"]),
            "cutover_receipt_count": sum(1 for study in report["studies"] if study["cutover_receipt"]["exists"]),
            "ai_reviewer_request_count": sum(
                1
                for study in report["studies"]
                if study["ai_reviewer_request"]["exists"]
            ),
            "noncanonical_residue_migration_count": len(residue_migrations),
            "noncanonical_residue_migrations": residue_migrations,
        }
    return report


def paper_authority_cutover_latest_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / MIGRATION_ROOT_RELPATH / "latest.json"


def stage_native_body_authority_root(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / BODY_ROOT_RELPATH


def resolve_body_authority_ref(*, study_root: Path, relative_path: Path) -> Path:
    resolved_study_root = Path(study_root).expanduser().resolve()
    direct = resolved_study_root / relative_path
    if direct.exists():
        return direct.resolve()
    staged = resolved_study_root / BODY_ROOT_RELPATH / relative_path
    return staged.resolve()


def paper_body_ref_payloads(*, study_root: Path) -> dict[str, dict[str, Any]]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    payloads: dict[str, dict[str, Any]] = {}
    for surface, candidates in PAPER_BODY_REF_SURFACES.items():
        if surface == "medical_prose_review":
            selected = _first_existing_body_ref(
                study_root=resolved_study_root,
                candidates=candidates,
            )
        else:
            selected = _first_existing_body_ref(
                study_root=resolved_study_root,
                candidates=candidates,
                prefer_stage_native=True,
            )
        if selected is None:
            selected = candidates[0]
        path = resolve_body_authority_ref(study_root=resolved_study_root, relative_path=selected)
        try:
            relative_path = path.relative_to(resolved_study_root).as_posix()
        except ValueError:
            relative_path = str(path)
        payloads[surface] = {
            "surface": surface,
            "relative_path": relative_path,
            "path": str(path),
            "required": True,
            "present": path.exists(),
            "valid": path.exists(),
            "authority_root": str(stage_native_body_authority_root(study_root=resolved_study_root)),
            "authority_surface": SURFACE_KIND,
        }
    return payloads


def read_paper_authority_cutover(*, study_root: Path) -> dict[str, Any] | None:
    return _read_json_object(paper_authority_cutover_latest_path(study_root=study_root))


def cutover_requires_ai_reviewer(*, study_root: Path) -> bool:
    resolved_study_root = Path(study_root).expanduser().resolve()
    payload = read_paper_authority_cutover(study_root=resolved_study_root)
    if not payload:
        return False
    status = _text(payload.get("status"))
    if status == "awaiting_new_mas_authority":
        return True
    if status == "new_mas_authority_established":
        return not _new_mas_authority_eval_current(study_root=resolved_study_root, receipt=payload)
    return False


def mark_cutover_new_mas_authority_established(
    *,
    study_root: Path,
    publication_eval_ref: str,
    eval_id: str,
    recorded_at: str | None = None,
) -> dict[str, Any] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    receipt = read_paper_authority_cutover(study_root=resolved_study_root)
    if not receipt:
        return None
    status = _text(receipt.get("status"))
    if status == "new_mas_authority_established" and _new_mas_authority_eval_current(
        study_root=resolved_study_root,
        receipt=receipt,
    ):
        return dict(receipt)
    if status not in {"awaiting_new_mas_authority", "new_mas_authority_established"}:
        return None
    timestamp = _text(recorded_at) or _utc_now()
    authority_boundary = dict(receipt.get("authority_boundary") or {})
    authority_boundary["quality_verdict_written"] = True
    authority_boundary["submission_package_regenerated"] = False
    updated = {
        **receipt,
        "status": "new_mas_authority_established",
        "new_mas_authority": {
            "owner": "ai_reviewer",
            "publication_eval_ref": publication_eval_ref,
            "eval_id": eval_id,
            "established_at": timestamp,
        },
        "authority_boundary": authority_boundary,
        "required_next_actions": ["publication_gate", "sync_study_delivery"],
    }
    _write_cutover_receipt(study_root=resolved_study_root, receipt=updated, recorded_at=timestamp)
    return updated


def cutover_publication_eval_payload(*, study_root: Path) -> dict[str, Any] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    payload = read_paper_authority_cutover(study_root=resolved_study_root)
    if not payload:
        return None
    status = _text(payload.get("status"))
    if status == "new_mas_authority_established" and _new_mas_authority_eval_current(
        study_root=resolved_study_root,
        receipt=payload,
    ):
        return None
    if status not in {"awaiting_new_mas_authority", "new_mas_authority_established"}:
        return None
    return {
        "schema_version": 1,
        "surface_kind": "paper_authority_cutover_projection",
        "assessment_provenance": {
            "owner": "paper_authority_cutover",
            "source_kind": "clean_migration_receipt",
            "ai_reviewer_required": True,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "gaps": [],
        "recommended_actions": [],
        "cutover_receipt_ref": str(paper_authority_cutover_latest_path(study_root=resolved_study_root)),
        "stage_native_body_authority_root": str(stage_native_body_authority_root(study_root=resolved_study_root)),
    }


def new_mas_authority_eval_current(*, study_root: Path) -> bool:
    payload = read_paper_authority_cutover(study_root=study_root)
    if not payload or _text(payload.get("status")) != "new_mas_authority_established":
        return False
    return _new_mas_authority_eval_current(study_root=Path(study_root).expanduser().resolve(), receipt=payload)


def _new_mas_authority_eval_current(*, study_root: Path, receipt: Mapping[str, Any]) -> bool:
    authority = receipt.get("new_mas_authority")
    if not isinstance(authority, Mapping):
        return False
    eval_id = _text(authority.get("eval_id"))
    publication_eval_ref = _text(authority.get("publication_eval_ref"))
    if eval_id is None or publication_eval_ref is None:
        return False
    expected_path = Path(publication_eval_ref).expanduser()
    if not expected_path.is_absolute():
        expected_path = study_root / expected_path
    expected_path = expected_path.resolve()
    active_path = (study_root / "artifacts" / "publication_eval" / "latest.json").resolve()
    if expected_path != active_path or not active_path.exists():
        return False
    active_eval = _read_json_object(active_path)
    if not active_eval:
        return False
    provenance = active_eval.get("assessment_provenance")
    if not isinstance(provenance, Mapping):
        return False
    return (
        _text(active_eval.get("eval_id")) == eval_id
        and _text(provenance.get("owner")) == "ai_reviewer"
        and provenance.get("ai_reviewer_required") is False
    )


def _resolve_study_ids(*, profile: WorkspaceProfile, study_ids: Iterable[str] | None) -> tuple[str, ...]:
    selected = tuple(item for raw in (study_ids or ()) if (item := _text(raw)) is not None)
    if selected:
        available_study_ids = set(_discover_paper_study_ids(profile))
        for study_id in selected:
            if study_id not in available_study_ids:
                known = ", ".join(sorted(available_study_ids)) or "<none>"
                raise ValueError(f"Unknown canonical paper authority study_id: {study_id}; known study_ids: {known}")
        return selected
    return _discover_paper_study_ids(profile)


def _discover_paper_study_ids(profile: WorkspaceProfile) -> tuple[str, ...]:
    supervised = list(study_identity.resolve_owner_route_reconcile_study_ids(profile))
    return tuple(supervised)


def _discover_noncanonical_paper_authority_residue_dirs(profile: WorkspaceProfile) -> list[dict[str, Any]]:
    if not profile.studies_root.is_dir():
        return []
    canonical_study_ids = set(study_identity.resolve_owner_route_reconcile_study_ids(profile))
    residue_dirs: list[dict[str, Any]] = []
    for study_root in sorted(path for path in profile.studies_root.iterdir() if path.is_dir()):
        if study_root.name in canonical_study_ids:
            continue
        surface_ids = [
            surface_id
            for surface_id, relpath, _ in (*LEGACY_BODY_SURFACES, *ACTIVE_SURFACES)
            if (study_root / relpath).exists()
        ]
        if not surface_ids:
            continue
        residue_dirs.append(
            {
                "study_id": study_root.name,
                "path": str(study_root.expanduser().resolve()),
                "reason": "paper_authority_surface_without_study_marker",
                "surface_ids": surface_ids,
            }
        )
    return residue_dirs


def _study_plan(*, profile: WorkspaceProfile, study_id: str, recorded_at: str) -> dict[str, Any]:
    study_root = (profile.studies_root / study_id).expanduser().resolve()
    archive_root = _archive_root(study_root=study_root, recorded_at=recorded_at)
    receipt = _read_json_object(paper_authority_cutover_latest_path(study_root=study_root))
    receipt_status = _text((receipt or {}).get("status"))
    authority_current = (
        receipt_status == "new_mas_authority_established"
        and receipt is not None
        and _new_mas_authority_eval_current(study_root=study_root, receipt=receipt)
    )
    authority_stale = receipt_status == "new_mas_authority_established" and not authority_current
    active_surfaces = (
        _legacy_body_surface_items(study_root=study_root)
        if receipt_status == "new_mas_authority_established"
        else _active_surface_items(study_root=study_root, receipt_status=receipt_status)
    )
    request_path = domain_action_request_lifecycle.stable_ai_reviewer_request_path(study_root=study_root)
    return {
        "study_id": study_id,
        "study_root": str(study_root),
        "cutover_required": bool(active_surfaces) or not bool(receipt) or authority_stale,
        "active_surfaces": active_surfaces,
        "archive_root": str(archive_root),
        "cutover_receipt": {
            "path": str(paper_authority_cutover_latest_path(study_root=study_root)),
            "exists": bool(receipt),
            "status": _text((receipt or {}).get("status")),
        },
        "ai_reviewer_request": {
            "path": str(request_path),
            "exists": request_path.exists(),
        },
        "next_required_actions": (
            ["return_to_ai_reviewer_workflow", "publication_gate", "sync_study_delivery"]
            if authority_stale
            else _study_next_actions(active_surfaces=active_surfaces, receipt=receipt)
        ),
    }


def _active_surface_items(*, study_root: Path, receipt_status: str | None = None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    items.extend(_legacy_body_surface_items(study_root=study_root))
    for surface_id, relpath, authority_role in ACTIVE_SURFACES:
        if (
            surface_id == "publication_eval_latest"
            and receipt_status == "awaiting_new_mas_authority"
            and _publication_eval_is_clean_migration_pending_surface(study_root / relpath)
        ):
            continue
        item = _surface_item(
            study_root=study_root,
            surface_id=surface_id,
            relpath=relpath,
            authority_role=authority_role,
            candidate_action="archive_as_provenance_only",
        )
        if item is not None:
            items.append(item)
    return items


def _legacy_body_surface_items(*, study_root: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for surface_id, relpath, authority_role in LEGACY_BODY_SURFACES:
        item = _surface_item(
            study_root=study_root,
            surface_id=surface_id,
            relpath=relpath,
            authority_role=authority_role,
            candidate_action="move_to_stage_native_body_authority",
        )
        if item is not None:
            items.append(item)
    return items


def _surface_item(
    *,
    study_root: Path,
    surface_id: str,
    relpath: Path,
    authority_role: str,
    candidate_action: str,
) -> dict[str, Any] | None:
    path = study_root / relpath
    if not path.exists():
        return None
    return {
        "surface_id": surface_id,
        "relative_path": relpath.as_posix(),
        "path": str(path),
        "kind": "directory" if path.is_dir() else "file",
        "authority_role": authority_role,
        "size_bytes": _surface_size(path),
        "sha256": _sha256(path) if path.is_file() else None,
        "candidate_action": candidate_action,
    }


def _publication_eval_is_clean_migration_pending_surface(path: Path) -> bool:
    payload = _read_json_object(path)
    if not payload:
        return False
    provenance = payload.get("assessment_provenance")
    if not isinstance(provenance, Mapping):
        return False
    owner = _text(provenance.get("owner"))
    if owner == "ai_reviewer":
        return _ai_reviewer_eval_is_clean_migration_interim(payload)
    if owner == "mechanical_projection":
        return _mechanical_eval_is_non_authoritative_projection(payload)
    return False


def _ai_reviewer_eval_is_clean_migration_interim(payload: Mapping[str, Any]) -> bool:
    if _text(payload.get("eval_id")) is None:
        return False
    provenance = payload.get("assessment_provenance")
    if not isinstance(provenance, Mapping):
        return False
    if _text(provenance.get("source_kind")) != "publication_eval_ai_reviewer":
        return False
    if provenance.get("ai_reviewer_required") is not False:
        return False
    if provenance.get("mechanical_projection_used_as_quality_authority") is not False:
        return False
    if not _has_clean_migration_rebuild_action(payload):
        return False
    reviewer_os = payload.get("reviewer_operating_system")
    if not isinstance(reviewer_os, Mapping):
        return False
    currentness = reviewer_os.get("currentness_checks")
    if not isinstance(currentness, Mapping):
        return False
    return _clean_migration_currentness_present(currentness)


def _mechanical_eval_is_non_authoritative_projection(payload: Mapping[str, Any]) -> bool:
    provenance = payload.get("assessment_provenance")
    if not isinstance(provenance, Mapping):
        return False
    return (
        _text(provenance.get("source_kind")) == "publication_gate_report"
        and _text(provenance.get("policy_id")) == "publication_gate_projection_v1"
        and provenance.get("ai_reviewer_required") is True
        and provenance.get("mechanical_projection_used_as_quality_authority") is False
    )


def _clean_migration_currentness_present(currentness: Mapping[str, Any]) -> bool:
    for key in ("medical_prose_review", "current_package_freshness"):
        value = currentness.get(key)
        if isinstance(value, Mapping) and _text(value.get("authority_source_signature")) == SURFACE_KIND:
            return True
    return False


def _has_clean_migration_rebuild_action(payload: Mapping[str, Any]) -> bool:
    for action in payload.get("recommended_actions") or ():
        if not isinstance(action, Mapping):
            continue
        if _text(action.get("action_id")) == "paper-authority-clean-migration-rebuild":
            return True
    for gap in payload.get("gaps") or ():
        if not isinstance(gap, Mapping):
            continue
        if _text(gap.get("gap_id")) == "paper-authority-clean-migration":
            return True
    return False


def _apply_study_cutover(*, profile: WorkspaceProfile, study_plan: Mapping[str, Any], recorded_at: str) -> None:
    study_root = Path(str(study_plan["study_root"]))
    active_surfaces = [item for item in study_plan.get("active_surfaces") or [] if isinstance(item, Mapping)]
    archive_root = _archive_root(study_root=study_root, recorded_at=recorded_at)
    archive_root.mkdir(parents=True, exist_ok=True)
    archived = []
    for item in active_surfaces:
        relpath = Path(str(item["relative_path"]))
        source = study_root / relpath
        if not source.exists():
            continue
        if str(item.get("candidate_action") or "") == "move_to_stage_native_body_authority":
            destination = study_root / BODY_ROOT_RELPATH / relpath
        else:
            destination = archive_root / relpath
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            raise FileExistsError(f"paper authority archive destination already exists: {destination}")
        shutil.move(str(source), str(destination))
        archived.append({**dict(item), "archive_path": str(destination), "stage_native_path": str(destination)})
    receipt = _receipt_payload(
        profile=profile,
        study_root=study_root,
        study_id=str(study_plan["study_id"]),
        recorded_at=recorded_at,
        archive_root=archive_root,
        archived=archived,
    )
    _write_cutover_receipt(study_root=study_root, receipt=receipt, recorded_at=recorded_at)
    _materialize_ai_reviewer_request(study_root=study_root, receipt=receipt)


def _receipt_payload(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    study_id: str,
    recorded_at: str,
    archive_root: Path,
    archived: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "surface_kind": SURFACE_KIND,
        "status": "awaiting_new_mas_authority",
        "recorded_at": recorded_at,
        "workspace_root": str(profile.workspace_root.expanduser().resolve()),
        "study_id": study_id,
        "study_root": str(study_root),
        "archive_root": str(archive_root),
        "authority_boundary": {
            "legacy_reader_normalization": True,
            "paper_content_mutation": False,
            "canonical_paper_mutation": False,
            "quality_verdict_written": False,
            "submission_package_regenerated": False,
            "active_truth_surfaces_archived": True,
        },
        "stage_native_body_authority_root": str(stage_native_body_authority_root(study_root=study_root)),
        "archived_surfaces": archived,
        "retained_input_surfaces": _retained_input_surfaces(study_root=study_root),
        "legacy_artifacts_role": "provenance_only",
        "required_next_actions": _study_next_actions(active_surfaces=archived, receipt=None),
    }


def _write_cutover_receipt(*, study_root: Path, receipt: Mapping[str, Any], recorded_at: str) -> None:
    root = study_root / MIGRATION_ROOT_RELPATH
    history_root = study_root / HISTORY_ROOT_RELPATH
    history_root.mkdir(parents=True, exist_ok=True)
    history_path = history_root / f"{_history_stamp(recorded_at)}.json"
    latest_path = root / "latest.json"
    payload = {
        **dict(receipt),
        "latest_path": str(latest_path),
        "history_path": str(history_path),
    }
    history_path.write_text(_json_dumps(payload), encoding="utf-8")
    latest_path.write_text(_json_dumps(payload), encoding="utf-8")


def _materialize_ai_reviewer_request(*, study_root: Path, receipt: Mapping[str, Any]) -> None:
    input_refs = domain_action_request_lifecycle.default_ai_reviewer_request_input_refs(study_root=study_root)
    input_refs.update(paper_body_ref_payloads(study_root=study_root))
    input_refs["publication_gate_projection"] = {
        "surface": "publication_gate_projection",
        "path": str(study_root / MIGRATION_ROOT_RELPATH / "latest.json"),
        "relative_path": (MIGRATION_ROOT_RELPATH / "latest.json").as_posix(),
        "required": True,
        "present": True,
        "valid": True,
    }
    packet = domain_action_requests.build_ai_reviewer_publication_eval_request(
        study_id=str(receipt["study_id"]),
        quest_id=None,
        source_surface="paper_authority_clean_migration",
        workflow_state={
            "quality_authority": {
                "owner": "paper_authority_cutover",
                "state": "awaiting_new_mas_authority",
            },
            "route_back": {"required": True, "target": "ai_reviewer"},
            "blockers": ["paper_authority_clean_migration_required"],
        },
        input_refs=input_refs,
    )
    packet["paper_authority_cutover_ref"] = str(study_root / MIGRATION_ROOT_RELPATH / "latest.json")
    packet["stage_native_body_authority_root"] = str(stage_native_body_authority_root(study_root=study_root))
    packet["target_assessment_owner"] = "ai_reviewer"
    packet["may_authorize_quality_gate"] = False
    domain_action_request_lifecycle.materialize_ai_reviewer_request(
        study_root=study_root,
        packet=packet,
    )


def _apply_noncanonical_residue_cutover(
    *,
    profile: WorkspaceProfile,
    residue_dirs: list[dict[str, Any]],
    recorded_at: str,
) -> list[dict[str, Any]]:
    migrations: list[dict[str, Any]] = []
    if not residue_dirs:
        return migrations
    workspace_root = profile.workspace_root.expanduser().resolve()
    history_root = workspace_root / NONCANONICAL_RESIDUE_HISTORY_ROOT_RELPATH / _history_stamp(recorded_at)
    for residue in residue_dirs:
        source = Path(str(residue["path"])).expanduser().resolve()
        if not source.exists():
            continue
        destination = history_root / source.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            raise FileExistsError(f"noncanonical paper residue destination already exists: {destination}")
        shutil.move(str(source), str(destination))
        migrations.append(
            {
                "study_id": str(residue["study_id"]),
                "source_path": str(source),
                "stage_native_archive_path": str(destination),
                "surface_ids": list(residue.get("surface_ids") or ()),
                "reason": "noncanonical_paper_authority_surface_without_study_marker",
            }
        )
    if migrations:
        _write_noncanonical_residue_receipt(
            workspace_root=workspace_root,
            recorded_at=recorded_at,
            migrations=migrations,
        )
    return migrations


def _write_noncanonical_residue_receipt(
    *,
    workspace_root: Path,
    recorded_at: str,
    migrations: list[dict[str, Any]],
) -> None:
    root = workspace_root / NONCANONICAL_RESIDUE_ROOT_RELPATH
    history_root = workspace_root / NONCANONICAL_RESIDUE_HISTORY_ROOT_RELPATH
    latest_path = root / "latest.json"
    history_path = history_root / f"{_history_stamp(recorded_at)}.json"
    payload = {
        "schema_version": 1,
        "surface_kind": "noncanonical_paper_authority_residue_migration",
        "recorded_at": recorded_at,
        "workspace_root": str(workspace_root),
        "status": "migrated_to_stage_native_body_authority_archive",
        "migration_count": len(migrations),
        "migrations": migrations,
        "authority_boundary": {
            "study_truth_created": False,
            "paper_content_mutation": False,
            "canonical_paper_mutation": False,
            "quality_verdict_written": False,
        },
        "latest_path": str(latest_path),
        "history_path": str(history_path),
    }
    history_path.parent.mkdir(parents=True, exist_ok=True)
    latest_path.parent.mkdir(parents=True, exist_ok=True)
    history_path.write_text(_json_dumps(payload), encoding="utf-8")
    latest_path.write_text(_json_dumps(payload), encoding="utf-8")


def _study_next_actions(*, active_surfaces: list[Mapping[str, Any]], receipt: Mapping[str, Any] | None) -> list[str]:
    if active_surfaces:
        return [
            "archive_legacy_paper_authority_surfaces",
            "return_to_ai_reviewer_workflow",
            "publication_gate",
            "sync_study_delivery",
        ]
    if not receipt:
        return ["return_to_ai_reviewer_workflow"]
    if _text(receipt.get("status")) == "awaiting_new_mas_authority":
        return ["return_to_ai_reviewer_workflow", "publication_gate", "sync_study_delivery"]
    return []


def _workspace_next_actions(studies: list[Mapping[str, Any]]) -> list[str]:
    actions: list[str] = []
    for study in studies:
        for action in study.get("next_required_actions") or []:
            if isinstance(action, str) and action not in actions:
                actions.append(action)
    return actions


def _archive_root(*, study_root: Path, recorded_at: str) -> Path:
    return study_root / HISTORY_ROOT_RELPATH / _history_stamp(recorded_at) / "active_surfaces"


def _retained_input_surfaces(*, study_root: Path) -> list[str]:
    refs = paper_body_ref_payloads(study_root=study_root)
    retained = [
        "artifacts/publication_eval/medical_prose_review.json",
        "artifacts/publication_eval/medical_prose_review_request.json",
    ]
    for payload in refs.values():
        relative_path = _text(payload.get("relative_path"))
        if relative_path and relative_path not in retained:
            retained.append(relative_path)
    return retained


def _first_existing_body_ref(
    *,
    study_root: Path,
    candidates: tuple[Path, ...],
    prefer_stage_native: bool = False,
) -> Path | None:
    roots = (
        (study_root / BODY_ROOT_RELPATH, study_root)
        if prefer_stage_native
        else (study_root, study_root / BODY_ROOT_RELPATH)
    )
    for root in roots:
        for candidate in candidates:
            if (root / candidate).exists():
                return candidate
    return None


def _surface_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            total += child.stat().st_size
    return total


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _history_stamp(recorded_at: str) -> str:
    return recorded_at.replace("+00:00", "Z").replace("+0000", "Z").replace("-", "").replace(":", "").replace(".", "")


def _json_dumps(payload: Mapping[str, Any]) -> str:
    return json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "cutover_publication_eval_payload",
    "cutover_requires_ai_reviewer",
    "mark_cutover_new_mas_authority_established",
    "new_mas_authority_eval_current",
    "paper_authority_cutover_latest_path",
    "paper_body_ref_payloads",
    "read_paper_authority_cutover",
    "resolve_body_authority_ref",
    "run_paper_authority_clean_migration",
    "stage_native_body_authority_root",
]
