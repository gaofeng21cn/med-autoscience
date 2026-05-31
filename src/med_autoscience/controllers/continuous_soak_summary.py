from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import (
    artifact_lifecycle_operations_report,
    workspace_authority_migration_audit,
)


SCHEMA_VERSION = 1
SURFACE = "continuous_soak_summary"


def build_continuous_soak_summary(
    *,
    workspace_roots: Iterable[str | Path],
    deep: bool = False,
    max_files: int | None = None,
    max_seconds: float | None = None,
) -> dict[str, Any]:
    roots = [Path(root) for root in workspace_roots]
    lifecycle_report = artifact_lifecycle_operations_report.run_lifecycle_operations_report(
        workspace_roots=roots,
        deep=deep,
        max_files=max_files,
        max_seconds=max_seconds,
    )
    migration_report = workspace_authority_migration_audit.run_migration_audit(
        workspace_roots=roots,
        dry_run=True,
    )
    governance = _mapping(lifecycle_report.get("storage_governance_policy"))
    mutation_policy = _mapping(lifecycle_report.get("mutation_policy"))
    cleanup_plan = _mapping(lifecycle_report.get("cleanup_plan"))
    retention_plan = _mapping(lifecycle_report.get("retention_plan"))
    backfill_blockers = _backfill_blockers(migration_report)
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "workspace_count": _int(migration_report.get("workspace_count")),
        "study_count": _int(migration_report.get("study_count")),
        "mutating_actions": _int(_mapping(migration_report.get("action_counts")).get("mutating")),
        "unclassified_authority_surface": _int(migration_report.get("unclassified_authority_surface")),
        "writes_workspace": bool(mutation_policy.get("writes_workspace")) or bool(cleanup_plan.get("writes_workspace")),
        **_receipt_ref_family_summary(retention_plan),
        "top_growth_buckets": _sequence(governance.get("top_growth_buckets")),
        "backfill_blockers": backfill_blockers,
        "next_safe_action": _mapping(governance.get("next_safe_action")),
        "artifact_authority_boundary": {
            "summary_only": True,
            "body_free": True,
            "read_only": True,
            "writes_workspace": False,
            "physical_cleanup_performed": False,
            "can_authorize_artifact_mutation": False,
            "can_authorize_cleanup_apply": False,
            "can_claim_domain_ready": False,
            "can_claim_production_ready": False,
        },
        "source_surfaces": {
            "migration_audit": migration_report.get("surface"),
            "lifecycle_report": lifecycle_report.get("surface"),
            "storage_governance_policy": governance.get("surface_kind"),
            "artifact_retention_plan": retention_plan.get("surface_kind"),
        },
        "read_only_contract": {
            "dry_run": True,
            "physical_cleanup_owned_by": "one-person-lab",
            "writes_workspace": False,
        },
    }


def _receipt_ref_family_summary(retention_plan: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "artifact_lifecycle_receipt_refs": _sequence(retention_plan.get("artifact_lifecycle_receipt_refs")),
        "artifact_lifecycle_receipt_ref_count": _int(retention_plan.get("artifact_lifecycle_receipt_ref_count")),
        "artifact_lifecycle_receipt_refs_truncated": bool(
            retention_plan.get("artifact_lifecycle_receipt_refs_truncated")
        ),
        "artifact_authority_receipt_refs": _sequence(retention_plan.get("artifact_authority_receipt_refs")),
        "artifact_authority_receipt_ref_count": _int(retention_plan.get("artifact_authority_receipt_ref_count")),
        "artifact_authority_receipt_refs_truncated": bool(
            retention_plan.get("artifact_authority_receipt_refs_truncated")
        ),
        "cleanup_receipt_refs": _sequence(retention_plan.get("cleanup_receipt_refs")),
        "cleanup_receipt_ref_count": _int(retention_plan.get("cleanup_receipt_ref_count")),
        "cleanup_receipt_refs_truncated": bool(retention_plan.get("cleanup_receipt_refs_truncated")),
        "restore_proof_refs": _sequence(retention_plan.get("restore_proof_refs")),
        "restore_proof_ref_count": _int(retention_plan.get("restore_proof_ref_count")),
        "restore_proof_refs_truncated": bool(retention_plan.get("restore_proof_refs_truncated")),
        "retention_receipt_refs": _sequence(retention_plan.get("retention_receipt_refs")),
        "retention_receipt_ref_count": _int(retention_plan.get("retention_receipt_ref_count")),
        "retention_receipt_refs_truncated": bool(retention_plan.get("retention_receipt_refs_truncated")),
        "artifact_lifecycle_apply_blocker_refs": _sequence(
            retention_plan.get("artifact_lifecycle_apply_blocker_refs")
        ),
        "artifact_lifecycle_apply_blocker_ref_count": _int(
            retention_plan.get("artifact_lifecycle_apply_blocker_ref_count")
        ),
        "artifact_lifecycle_apply_blocker_refs_truncated": bool(
            retention_plan.get("artifact_lifecycle_apply_blocker_refs_truncated")
        ),
        "artifact_lifecycle_apply_blocker_reason_counts": dict(
            _mapping(retention_plan.get("artifact_lifecycle_apply_blocker_reason_counts"))
        ),
        "artifact_lifecycle_apply_blocker_authority_boundary": dict(
            _mapping(retention_plan.get("artifact_lifecycle_apply_blocker_authority_boundary"))
        ),
        "physical_thinning_handoff": dict(_mapping(retention_plan.get("physical_thinning_handoff"))),
    }


def _backfill_blockers(migration_report: Mapping[str, Any]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for study in _sequence(migration_report.get("studies")):
        study_mapping = _mapping(study)
        plan = _mapping(study_mapping.get("historical_backfill_plan"))
        if not plan:
            continue
        blockers.append(
            {
                "workspace_style": _text(study_mapping.get("workspace_style")),
                "study_id": _text(study_mapping.get("study_id")),
                "plan_type": _text(plan.get("plan_type")),
                "missing_surfaces": _sequence(plan.get("missing_surfaces")),
                "writes_workspace": bool(_mapping(plan.get("mutation_policy")).get("writes_workspace")),
                "next_action": "rerun_publication_gate_after_canonical_regeneration",
            }
        )
    return blockers


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[Any]:
    return list(value) if isinstance(value, list | tuple) else []


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _int(value: object) -> int:
    if isinstance(value, bool):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


__all__ = ["SCHEMA_VERSION", "SURFACE", "build_continuous_soak_summary"]
