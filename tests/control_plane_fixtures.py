from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ControlPlaneFactCase:
    case_id: str
    payload: dict[str, Any]
    supervisor_tick_audit: dict[str, Any] | None
    expected: dict[str, Any]


def stale_continuation_run_id_case() -> ControlPlaneFactCase:
    return ControlPlaneFactCase(
        case_id="stale_continuation_run_id",
        payload={
            "quest_status": "active",
            "runtime_liveness_status": "unknown",
            "reason": "quest_marked_running_but_no_live_session",
            "continuation_state": {
                "quest_status": "running",
                "active_run_id": "run-stale-continuation",
            },
        },
        supervisor_tick_audit={"status": "stale"},
        expected={
            "active_run_id": "run-stale-continuation",
            "active_run_id_source": "continuation_state.active_run_id",
            "strict_live": False,
            "missing_live_session": True,
            "recovery_pending": True,
        },
    )


def active_run_projection_case() -> ControlPlaneFactCase:
    return ControlPlaneFactCase(
        case_id="active_run_projection",
        payload={
            "quest_status": "running",
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-live-projected",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-live-projected",
                    "worker_running": True,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
            "autonomous_runtime_notice": {"browser_url": "http://127.0.0.1:20999"},
        },
        supervisor_tick_audit={"status": "fresh"},
        expected={
            "active_run_id": "run-live-projected",
            "active_run_id_source": "runtime_liveness_audit.active_run_id",
            "runtime_liveness_status": "live",
            "strict_live": True,
            "worker_running": True,
            "worker_pending": False,
            "stop_requested": False,
            "recovery_pending": False,
        },
    )


def stale_gate_authority_case() -> ControlPlaneFactCase:
    return ControlPlaneFactCase(
        case_id="stale_gate_authority",
        payload={
            "quest_status": "running",
            "decision": "continue",
            "reason": "stale_submission_minimal_authority",
            "runtime_liveness_status": "live",
            "runtime_liveness_audit": {
                "status": "live",
                "runtime_audit": {
                    "active_run_id": "run-authority",
                    "worker_running": True,
                },
            },
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "current_required_action": "return_to_publishability_gate",
            },
        },
        supervisor_tick_audit={"status": "fresh"},
        expected={
            "active_run_id": "run-authority",
            "active_run_id_source": "runtime_audit.active_run_id",
            "strict_live": True,
            "missing_live_session": False,
            "recovery_pending": False,
        },
    )


def fact_cases() -> tuple[ControlPlaneFactCase, ...]:
    return (
        stale_continuation_run_id_case(),
        active_run_projection_case(),
        stale_gate_authority_case(),
    )


def supervisor_lightweight_payload() -> dict[str, Any]:
    return {
        "quest_status": "running",
        "runtime_liveness_status": "unknown",
        "execution_owner_guard": {
            "supervisor_only": True,
            "guard_reason": "live_managed_runtime",
            "active_run_id": "run-lightweight-live",
        },
        "autonomous_runtime_notice": {
            "notification_reason": "detected_existing_live_managed_runtime",
        },
        "continuation_state": {
            "quest_status": "running",
            "active_run_id": "run-lightweight-live",
        },
    }


def package_handoff_parked_status() -> dict[str, Any]:
    return {
        "quest_status": "stopped",
        "decision": "blocked",
        "reason": "quest_parked_on_unchanged_finalize_state",
        "publication_supervisor_state": {
            "supervisor_phase": "bundle_stage_ready",
            "current_required_action": "complete_bundle_stage",
            "bundle_tasks_downstream_only": False,
        },
    }


def external_upstream_parked_status() -> dict[str, Any]:
    return {
        "quest_status": "stopped",
        "decision": "blocked",
        "reason": "provider_rate_limit",
        "runtime_failure_classification": {
            "blocker_class": "external_upstream_unavailable",
            "action_mode": "external_fix_required",
            "requires_human_gate": True,
        },
    }


def same_fingerprint_status_payload() -> dict[str, Any]:
    return {
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "quest_status": "running",
        "decision": "continue",
        "reason": "stale_submission_minimal_authority",
        "runtime_liveness_status": "live",
        "runtime_liveness_audit": {
            "status": "live",
            "active_run_id": "run-live-fingerprint",
            "runtime_audit": {
                "active_run_id": "run-live-fingerprint",
                "worker_running": True,
            },
        },
        "publication_supervisor_state": {
            "supervisor_phase": "publishability_gate_blocked",
            "current_required_action": "return_to_publishability_gate",
        },
    }


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _write_text(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _delivery_manifest_lifecycle_hook(
    *, study_root: Path, current_package: Path, submission_minimal: Path
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "surface_kind": "study_delivery_sync_lifecycle",
        "authority_sync": {
            "surface_kind": "delivery_authority_sync",
            "status": "projection_only",
            "study_root": str(study_root),
            "direct_edit_allowed": False,
            "quality_authority_allowed": False,
            "dispatch_authority_allowed": False,
            "authority_source_roles": ["canonical_source"],
            "blocked_authority_paths": [
                str(current_package),
                str(current_package.with_suffix(".zip")),
                str(submission_minimal),
            ],
        },
        "lifecycle_roles": {
            "current_package": "derived_projection",
            "submission_minimal": "human_handoff_mirror",
            "zip": "derived_projection",
            "pdf": "derived_projection",
            "docx": "derived_projection",
        },
    }


def _delivery_manifest_publication_refs(
    *, paper_root: Path, current_package: Path, submission_minimal: Path
) -> dict[str, str]:
    return {
        "paper_root_ref": str(paper_root),
        "current_package_ref": str(current_package),
        "current_package_zip_ref": str(current_package.with_suffix(".zip")),
        "submission_minimal_ref": str(submission_minimal),
        "publication_eval_ref": str(paper_root.parent / "artifacts" / "publication_eval" / "latest.json"),
    }


def build_dm_cvd_migration_audit_fixture(root: Path) -> Path:
    workspace_root = root / "DM-CVD-Mortality-Risk"
    studies_root = workspace_root / "studies"

    for study_id in (
        "001-dm-cvd-mortality-risk",
        "003-dpcc-primary-care-phenotype-treatment-gap",
    ):
        study_root = studies_root / study_id
        paper_root = study_root / "paper"
        manuscript_root = study_root / "manuscript"
        current_package = manuscript_root / "current_package"
        submission_minimal = paper_root / "submission_minimal"
        _write_json(
            paper_root / "study_manifest.json",
            {
                "study_id": study_id,
                "surface": "study_manifest",
                "authority_owner": "controller",
            },
        )
        _write_json(
            manuscript_root / "delivery_manifest.json",
            {
                "study_id": study_id,
                "surface": "delivery_manifest",
                "authority_owner": "controller",
                "source_signature": f"sig-{study_id}",
                "authority_source_signature": f"sig-{study_id}",
                "surface_roles": {
                    "human_facing_current_package_root": str(current_package),
                    "human_facing_current_package_zip": str(current_package.with_suffix(".zip")),
                },
                "publication_refs": _delivery_manifest_publication_refs(
                    paper_root=paper_root,
                    current_package=current_package,
                    submission_minimal=submission_minimal,
                ),
                "artifact_lifecycle": _delivery_manifest_lifecycle_hook(
                    study_root=study_root,
                    current_package=current_package,
                    submission_minimal=submission_minimal,
                ),
            },
        )
        _write_json(
            submission_minimal / "submission_manifest.json",
            {
                "study_id": study_id,
                "surface": "submission_minimal_manifest",
                "authority_owner": "controller",
                "source_signature": f"sig-{study_id}",
                "authority_source_signature": f"sig-{study_id}",
            },
        )
        _write_text(current_package / "README.md", f"# {study_id}\n")
        _write_text(current_package.with_suffix(".zip"), "zip-placeholder\n")
        _write_text(submission_minimal / "paper.md", f"# {study_id} submission\n")

    _write_json(
        workspace_root / "product_entry_manifest.json",
        {
            "surface": "product_entry_manifest",
            "authority_owner": "controller",
            "studies": ["001-dm-cvd-mortality-risk", "003-dpcc-primary-care-phenotype-treatment-gap"],
        },
    )
    return workspace_root


def build_nf_pitnet_migration_audit_fixture(root: Path) -> Path:
    workspace_root = root / "NF-PitNET"

    for study_id in ("003-endocrine-burden-followup", "004-invasive-architecture"):
        study_root = workspace_root / "papers" / study_id
        paper_root = study_root / "paper"
        package_root = study_root / "manuscript" / "current_package"
        submission_root = paper_root / "submission_minimal"
        _write_json(
            paper_root / "study_manifest.json",
            {
                "study_id": study_id,
                "surface": "study_manifest",
                "authority_owner": "controller",
            },
        )
        _write_json(
            study_root / "manuscript" / "delivery_manifest.json",
            {
                "study_id": study_id,
                "surface": "delivery_manifest",
                "authority_owner": "controller",
                "source_signature": f"sig-{study_id}",
                "authority_source_signature": f"sig-{study_id}",
                "targets": {
                    "current_package_root": str(package_root),
                    "current_package_zip": str(package_root.with_suffix(".zip")),
                },
                "publication_refs": _delivery_manifest_publication_refs(
                    paper_root=paper_root,
                    current_package=package_root,
                    submission_minimal=submission_root,
                ),
                "artifact_lifecycle": _delivery_manifest_lifecycle_hook(
                    study_root=study_root,
                    current_package=package_root,
                    submission_minimal=submission_root,
                ),
            },
        )
        _write_json(
            submission_root / "submission_manifest.json",
            {
                "study_id": study_id,
                "surface": "submission_minimal_manifest",
                "authority_owner": "controller",
                "source_signature": f"sig-{study_id}",
                "authority_source_signature": f"sig-{study_id}",
            },
        )
        _write_text(package_root / "README.md", f"# {study_id}\n")
        _write_text(package_root.with_suffix(".zip"), "zip-placeholder\n")
        _write_text(submission_root / "paper.md", f"# {study_id} submission\n")

    _write_json(
        workspace_root / "workspace_manifest.json",
        {
            "surface": "workspace_manifest",
            "authority_owner": "controller",
            "studies": ["003-endocrine-burden-followup", "004-invasive-architecture"],
        },
    )
    return workspace_root


def build_migration_audit_fixture_with_runtime_noise(root: Path) -> Path:
    workspace_root = build_dm_cvd_migration_audit_fixture(root)
    _write_json(
        workspace_root / ".ds" / "runtime" / "quests" / "999-noise" / "paper" / "study_manifest.json",
        {
            "study_id": "999-runtime-noise",
            "surface": "study_manifest",
            "authority_owner": "controller",
        },
    )
    _write_json(
        workspace_root / ".git" / "objects" / "noise_manifest.json",
        {
            "study_id": "998-git-noise",
            "surface": "study_manifest",
            "authority_owner": "controller",
        },
    )
    _write_json(
        workspace_root / "data" / "raw" / "vendor_manifest.json",
        {
            "study_id": "997-data-noise",
            "surface": "dataset_manifest",
            "authority_owner": "controller",
        },
    )
    _write_json(
        workspace_root / "analysis" / "scratch" / "scratch_manifest.json",
        {
            "study_id": "996-analysis-noise",
            "surface": "scratch_manifest",
            "authority_owner": "controller",
        },
    )
    return workspace_root


def build_migration_audit_fixture_missing_submission_minimal(root: Path) -> Path:
    workspace_root = root / "DM-CVD-Missing-Submission"
    study_id = "005-delivery-projection-rebuild"
    study_root = workspace_root / "studies" / study_id
    paper_root = study_root / "paper"
    manuscript_root = study_root / "manuscript"
    current_package = manuscript_root / "current_package"

    _write_json(
        paper_root / "study_manifest.json",
        {
            "study_id": study_id,
            "surface": "study_manifest",
            "authority_owner": "controller",
        },
    )
    _write_json(
        manuscript_root / "delivery_manifest.json",
        {
            "study_id": study_id,
            "surface": "delivery_manifest",
            "authority_owner": "controller",
            "source_signature": f"sig-{study_id}",
            "authority_source_signature": f"sig-{study_id}",
            "surface_roles": {
                "human_facing_current_package_root": str(current_package),
                "human_facing_current_package_zip": str(current_package.with_suffix(".zip")),
            },
            "publication_refs": _delivery_manifest_publication_refs(
                paper_root=paper_root,
                current_package=current_package,
                submission_minimal=paper_root / "submission_minimal",
            ),
            "artifact_lifecycle": _delivery_manifest_lifecycle_hook(
                study_root=study_root,
                current_package=current_package,
                submission_minimal=paper_root / "submission_minimal",
            ),
        },
    )
    _write_text(current_package / "README.md", f"# {study_id}\n")
    _write_text(current_package.with_suffix(".zip"), "zip-placeholder\n")
    return workspace_root


def build_migration_audit_fixture_missing_delivery_lifecycle_hook(root: Path) -> Path:
    workspace_root = root / "DM-CVD-Missing-Lifecycle-Hook"
    study_id = "006-delivery-lifecycle-hook-backfill"
    study_root = workspace_root / "studies" / study_id
    paper_root = study_root / "paper"
    manuscript_root = study_root / "manuscript"
    current_package = manuscript_root / "current_package"
    submission_minimal = paper_root / "submission_minimal"

    _write_json(
        paper_root / "study_manifest.json",
        {
            "study_id": study_id,
            "surface": "study_manifest",
            "authority_owner": "controller",
        },
    )
    _write_json(
        manuscript_root / "delivery_manifest.json",
        {
            "study_id": study_id,
            "surface": "delivery_manifest",
            "authority_owner": "controller",
            "source_signature": f"sig-{study_id}",
            "authority_source_signature": f"sig-{study_id}",
            "surface_roles": {
                "human_facing_current_package_root": str(current_package),
                "human_facing_current_package_zip": str(current_package.with_suffix(".zip")),
            },
        },
    )
    _write_json(
        submission_minimal / "submission_manifest.json",
        {
            "study_id": study_id,
            "surface": "submission_minimal_manifest",
            "authority_owner": "controller",
            "source_signature": f"sig-{study_id}",
            "authority_source_signature": f"sig-{study_id}",
        },
    )
    _write_text(current_package / "README.md", f"# {study_id}\n")
    _write_text(current_package.with_suffix(".zip"), "zip-placeholder\n")
    _write_text(submission_minimal / "paper.md", f"# {study_id} submission\n")
    return workspace_root
