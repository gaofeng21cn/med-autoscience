from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from med_autoscience.controllers import paper_progress_degradation_evidence
from med_autoscience.controllers import real_paper_autonomy_soak_inventory
from med_autoscience.controllers import real_workspace_soak_monitor
from med_autoscience.controllers import domain_action_request_materializer
from med_autoscience.controllers import domain_owner_action_dispatch
from med_autoscience.controllers import domain_route_reconcile
from med_autoscience.controllers import owner_route_reconcile
from med_autoscience.controllers import workspace_monolith_migration
from med_autoscience.profiles import WorkspaceProfile, load_profile


SURFACE = "paper_autonomy_stability_evidence"
SCHEMA_VERSION = 1
READ_MODEL = "paper_autonomy_stability_evidence_read_model"

READ_ONLY_CONTRACT = {
    "mode": "read_only_evidence",
    "writes_real_workspace": False,
    "can_mutate_runtime": False,
    "can_write_current_package": False,
    "can_write_publication_eval": False,
    "can_write_controller_decisions": False,
    "can_write_runtime_sqlite": False,
    "can_write_restore_archive": False,
    "allowed_actions": [
        "read_profiles",
        "read_status_surfaces",
        "run_reconcile_domain_routes_dry_run_without_receipt_write",
        "run_workspace_migration_dry_run",
        "build_real_workspace_soak_monitor_read_model",
    ],
    "prohibited_actions": [
        "runtime_relaunch",
        "reconcile_domain_routes_receipt_write",
        "workspace_migration_apply",
        "current_package_write",
        "publication_eval_write",
        "controller_decisions_write",
        "runtime_sqlite_write",
        "restore_archive_write",
    ],
}


def build_paper_autonomy_stability_evidence(
    *,
    yang_root: str | Path = real_paper_autonomy_soak_inventory.DEFAULT_YANG_ROOT,
    profile_paths: Sequence[str | Path] | None = None,
    study_ids: Sequence[str] = (),
) -> dict[str, Any]:
    inventory = real_paper_autonomy_soak_inventory.build_real_paper_autonomy_soak_inventory(
        yang_root=yang_root,
        profile_paths=profile_paths,
    )
    profile_reports = [
        _profile_evidence(report, requested_study_ids=study_ids)
        for report in _sequence(inventory.get("profiles"))
        if isinstance(report, Mapping)
    ]
    blockers = [
        blocker
        for profile in profile_reports
        for blocker in _sequence(profile.get("blockers"))
        if isinstance(blocker, Mapping)
    ]
    progress_degradation = paper_progress_degradation_evidence.build_paper_progress_degradation_evidence(
        [
            dict(evidence)
            for profile in profile_reports
            if isinstance((evidence := profile.get("paper_progress_degradation_evidence")), Mapping)
        ]
    )
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "read_model": READ_MODEL,
        "mode": "read_only_evidence",
        "read_only_contract": dict(READ_ONLY_CONTRACT),
        "inventory_surface": {
            "surface": inventory.get("surface"),
            "mode": inventory.get("mode"),
            "profile_count": inventory.get("profile_count"),
            "summary": inventory.get("summary"),
        },
        "profile_count": len(profile_reports),
        "profiles": profile_reports,
        "paper_progress_degradation_evidence": progress_degradation,
        "summary": {
            "profiles_readable": sum(profile.get("profile_readable") is True for profile in profile_reports),
            "profiles_blocked": sum(bool(profile.get("blockers")) for profile in profile_reports),
            "blocker_count": len(blockers),
            "can_claim_landed": False,
            "writes_performed": False,
        },
        "blockers": blockers,
        "next_actions": _next_actions(blockers),
    }


def _profile_evidence(
    report: Mapping[str, Any],
    *,
    requested_study_ids: Sequence[str],
) -> dict[str, Any]:
    base = {
        "profile_path": _text(report.get("profile_path")),
        "profile_readable": report.get("profile_readable") is True,
        "profile_error": _text(report.get("profile_error")),
        "workspace_root": _text(report.get("workspace_root")),
        "migration_readiness": _text(report.get("migration_readiness")),
        "status_progress_readability": _mapping(report.get("status_progress_readability")),
        "studies": _study_lifecycle_evidence(report),
        "legacy_mds_diagnostic": _legacy_mds_diagnostic(report),
    }
    if not base["profile_readable"]:
        blocker = _blocker(
            kind="profile",
            reason="profile_unreadable",
            next_action="repair_or_select_readable_profile",
            profile_path=base["profile_path"],
        )
        return {
            **base,
            "reconcile_domain_routes_dry_run": _skipped("profile_unreadable"),
            "workspace_migration_dry_run": _skipped("profile_unreadable"),
            "real_workspace_soak_monitor": _skipped("profile_unreadable"),
            "paper_progress_degradation_evidence": _skipped("profile_unreadable"),
            "blockers": [blocker],
            "can_claim_landed": False,
        }

    profile_path = Path(base["profile_path"]).expanduser().resolve()
    try:
        profile = load_profile(profile_path)
    except Exception as exc:  # pragma: no cover - inventory already normalizes parser errors.
        blocker = _blocker(
            kind="profile",
            reason=f"{type(exc).__name__}: {exc}",
            next_action="repair_or_select_readable_profile",
            profile_path=str(profile_path),
        )
        return {
            **base,
            "profile_readable": False,
            "profile_error": blocker["reason"],
            "reconcile_domain_routes_dry_run": _skipped("profile_unreadable"),
            "workspace_migration_dry_run": _skipped("profile_unreadable"),
            "real_workspace_soak_monitor": _skipped("profile_unreadable"),
            "paper_progress_degradation_evidence": _skipped("profile_unreadable"),
            "blockers": [blocker],
            "can_claim_landed": False,
        }

    studies = [study for study in _sequence(report.get("studies")) if isinstance(study, Mapping)]
    resolved_study_ids = _resolved_study_ids(
        profile=profile,
        studies=studies,
        requested_study_ids=requested_study_ids,
    )
    reconcile = _reconcile_domain_routes_dry_run(profile=profile, study_ids=resolved_study_ids)
    migration = _workspace_migration_dry_run(profile_path=profile_path)
    monitor = _workspace_soak_monitor(studies=studies)
    progress_degradation = paper_progress_degradation_evidence.build_profile_progress_degradation_evidence(
        profile_path=str(profile_path),
        profile=profile,
        studies=studies,
        reconcile=reconcile,
        monitor=monitor,
    )
    blockers = _profile_blockers(
        profile_path=str(profile_path),
        studies=studies,
        reconcile=reconcile,
        migration=migration,
        monitor=monitor,
    )
    blockers.extend(
        dict(blocker)
        for blocker in _sequence(progress_degradation.get("blockers"))
        if isinstance(blocker, Mapping)
    )
    return {
        **base,
        "resolved_study_ids": list(resolved_study_ids),
        "reconcile_domain_routes_dry_run": reconcile,
        "workspace_migration_dry_run": migration,
        "real_workspace_soak_monitor": monitor,
        "paper_progress_degradation_evidence": progress_degradation,
        "blockers": blockers,
        "can_claim_landed": False,
    }


def _reconcile_domain_routes_dry_run(
    *,
    profile: WorkspaceProfile,
    study_ids: Sequence[str],
) -> dict[str, Any]:
    try:
        before_scan = owner_route_reconcile.scan_domain_routes(
            profile=profile,
            study_ids=study_ids,
            apply_safe_actions=False,
            apply_runtime_platform_repair=False,
            developer_supervisor_mode="developer_apply_safe",
            persist_surfaces=False,
        )
        consumed = domain_action_request_materializer.materialize_domain_action_requests(
            profile=profile,
            study_ids=study_ids,
            mode="developer_apply_safe",
            apply=False,
        )
        executed = domain_owner_action_dispatch.dispatch_domain_owner_actions(
            profile=profile,
            study_ids=study_ids,
            action_types=(),
            mode="developer_apply_safe",
            apply=False,
        )
        resolved = domain_route_reconcile._resolve_study_ids(  # noqa: SLF001
            requested=study_ids,
            before_scan=before_scan,
            after_scan={},
            consumed=consumed,
            executed=executed,
        )
        after_scan = owner_route_reconcile.scan_domain_routes(
            profile=profile,
            study_ids=resolved,
            apply_safe_actions=False,
            apply_runtime_platform_repair=False,
            developer_supervisor_mode="developer_apply_safe",
            persist_surfaces=False,
        )
        step_receipts = domain_route_reconcile._step_receipts(  # noqa: SLF001
            before_scan=before_scan,
            consumed=consumed,
            executed=executed,
            after_scan=after_scan,
        )
        study_receipts = [
            {
                "study_id": study_id,
                "before": domain_route_reconcile._study_projection(before_scan, study_id),  # noqa: SLF001
                "after": domain_route_reconcile._study_projection(after_scan, study_id),  # noqa: SLF001
            }
            for study_id in resolved
        ]
    except Exception as exc:
        return {
            "status": "blocked",
            "can_complete": False,
            "dry_run": True,
            "writes_performed": False,
            "reason": f"{type(exc).__name__}: {exc}",
            "next_action": "repair_runtime_truth_or_profile_inputs",
        }
    return {
        "status": "completed",
        "can_complete": True,
        "dry_run": True,
        "writes_performed": False,
        "requested_studies": list(study_ids),
        "resolved_studies": list(resolved),
        "step_receipts": step_receipts,
        "study_receipts": study_receipts,
        "blocked_count": executed.get("blocked_count"),
        "execution_count": executed.get("execution_count"),
        "stable_blockers": _stable_blockers(after_scan),
    }


def _workspace_migration_dry_run(profile_path: Path) -> dict[str, Any]:
    try:
        payload = workspace_monolith_migration.run_workspace_monolith_migration(
            profile_path=profile_path,
            apply=False,
        )
    except Exception as exc:
        return {
            "status": "blocked",
            "can_complete": False,
            "dry_run": True,
            "writes_performed": False,
            "reason": f"{type(exc).__name__}: {exc}",
            "next_action": "repair_workspace_migration_inputs",
        }
    skipped = [dict(item) for item in _sequence(payload.get("skipped")) if isinstance(item, Mapping)]
    migrated = [dict(item) for item in _sequence(payload.get("migrated")) if isinstance(item, Mapping)]
    duplicate = [dict(item) for item in _sequence(payload.get("duplicate")) if isinstance(item, Mapping)]
    status = "appliable" if migrated and not duplicate else "skipped" if skipped or not migrated else "blocked"
    if duplicate:
        status = "blocked"
    return {
        "status": status,
        "can_complete": True,
        "dry_run": True,
        "writes_performed": False,
        "appliable_count": len(migrated),
        "skipped_count": len(skipped),
        "duplicate_count": len(duplicate),
        "skipped_reasons": _reason_counts(skipped),
        "appliable_reasons": _reason_counts(migrated),
        "duplicate_reasons": _reason_counts(duplicate),
        "mutation_policy": payload.get("mutation_policy"),
    }


def _workspace_soak_monitor(*, studies: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    study_roots = [_text(study.get("study_root")) for study in studies if _text(study.get("study_root"))]
    if not study_roots:
        return _skipped("no_discovered_studies")
    try:
        payload = real_workspace_soak_monitor.build_real_workspace_soak_monitor(study_roots=study_roots)
    except Exception as exc:
        return {
            "status": "blocked",
            "can_complete": False,
            "writes_performed": False,
            "reason": f"{type(exc).__name__}: {exc}",
            "next_action": "repair_real_workspace_soak_inputs",
        }
    return {
        "status": payload.get("overall_status"),
        "can_complete": True,
        "writes_performed": False,
        "next_action": payload.get("next_action"),
        "blocked_reason_summary": payload.get("blocked_reason_summary"),
        "route_decision_summary": payload.get("route_decision_summary"),
        "action_cards": payload.get("action_cards"),
        "study_count": len(_sequence(payload.get("studies"))),
    }


def _profile_blockers(
    *,
    profile_path: str,
    studies: Sequence[Mapping[str, Any]],
    reconcile: Mapping[str, Any],
    migration: Mapping[str, Any],
    monitor: Mapping[str, Any],
) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    for study in studies:
        status = _text(study.get("status"))
        if status == "active":
            blockers.append(
                _blocker(
                    kind="runtime_truth",
                    reason=_text(study.get("reason")) or "active_study_present",
                    next_action="keep_supervisor_observing_active_runtime",
                    profile_path=profile_path,
                    study_id=_text(study.get("study_id")),
                )
            )
        elif status in {"parked", "inactive", "status_unreadable", "readable_unknown"}:
            blockers.append(
                _blocker(
                    kind="runtime_truth",
                    reason=_text(study.get("reason")) or status,
                    next_action="resolve_or_document_runtime_truth_before_landing",
                    profile_path=profile_path,
                    study_id=_text(study.get("study_id")),
                )
            )
    if reconcile.get("can_complete") is not True:
        blockers.append(
            _blocker(
                kind="runtime_truth",
                reason=_text(reconcile.get("reason")) or "reconcile_domain_routes_dry_run_blocked",
                next_action=_text(reconcile.get("next_action")) or "repair_runtime_truth_or_profile_inputs",
                profile_path=profile_path,
            )
        )
    for stable_blocker in _sequence(reconcile.get("stable_blockers")):
        if not isinstance(stable_blocker, Mapping):
            continue
        blockers.append(
            _blocker(
                kind=_text(stable_blocker.get("kind")) or "runtime_truth",
                reason=_text(stable_blocker.get("reason")) or _text(stable_blocker.get("status")) or "stable_blocker",
                next_action=_text(stable_blocker.get("next_action")) or "resolve_stable_blocker",
                profile_path=profile_path,
                study_id=_text(stable_blocker.get("study_id")),
            )
        )
    if migration.get("can_complete") is not True:
        blockers.append(
            _blocker(
                kind="runtime_truth",
                reason=_text(migration.get("reason")) or "workspace_migration_dry_run_blocked",
                next_action=_text(migration.get("next_action")) or "repair_workspace_migration_inputs",
                profile_path=profile_path,
            )
        )
    if monitor.get("status") in {"blocked", "partial"}:
        blockers.append(
            _blocker(
                kind="publication_truth",
                reason=f"real_workspace_soak_monitor:{_text(monitor.get('status'))}",
                next_action=_text(monitor.get("next_action")) or "resolve_real_workspace_soak_monitor_gaps",
                profile_path=profile_path,
            )
        )
    return blockers


def _study_lifecycle_evidence(report: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "study_id": _text(study.get("study_id")),
            "study_root": _text(study.get("study_root")),
            "status": _text(study.get("status")),
            "reason": _text(study.get("reason")),
            "active_run_id": _text(study.get("active_run_id")),
            "status_progress_readable": study.get("status_progress_readable") is True,
            "readable_surface_count": study.get("readable_surface_count"),
        }
        for study in _sequence(report.get("studies"))
        if isinstance(study, Mapping)
    ]


def _legacy_mds_diagnostic(report: Mapping[str, Any]) -> dict[str, Any]:
    evidence = [dict(item) for item in _sequence(report.get("legacy_mds_evidence")) if isinstance(item, Mapping)]
    return {
        "diagnostic_only": True,
        "default_runner_can_launch_runtime": False,
        "legacy_launcher_can_launch_runtime": False,
        "evidence_count": len(evidence),
        "evidence": evidence,
    }


def _resolved_study_ids(
    *,
    profile: WorkspaceProfile,
    studies: Sequence[Mapping[str, Any]],
    requested_study_ids: Sequence[str],
) -> tuple[str, ...]:
    requested = tuple(item for item in (_text(study_id) for study_id in requested_study_ids) if item)
    if requested:
        return requested
    from_inventory = tuple(
        item
        for item in (_text(study.get("study_id")) for study in studies)
        if item
    )
    if from_inventory:
        return from_inventory
    return owner_route_reconcile.resolve_owner_route_reconcile_study_ids(profile)


def _stable_blockers(scan_payload: Mapping[str, Any]) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = []
    for study in _sequence(scan_payload.get("studies")):
        if not isinstance(study, Mapping):
            continue
        stable = study.get("stable_blocker") or study.get("block_state") or study.get("current_blocker")
        if not isinstance(stable, Mapping):
            continue
        blockers.append(
            {
                "study_id": _text(study.get("study_id")),
                "kind": _text(stable.get("kind")) or _text(stable.get("blocker_kind")) or "runtime_truth",
                "status": _text(stable.get("status")),
                "reason": _text(stable.get("reason")) or _text(stable.get("blocked_reason")),
                "next_action": _text(stable.get("next_action")),
            }
        )
    return blockers


def _reason_counts(items: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        reason = _text(item.get("reason")) or "unspecified"
        counts[reason] = counts.get(reason, 0) + 1
    return counts


def _next_actions(blockers: Sequence[Mapping[str, Any]]) -> list[str]:
    actions: list[str] = []
    for blocker in blockers:
        action = _text(blocker.get("next_action"))
        if action and action not in actions:
            actions.append(action)
    return actions


def _blocker(
    *,
    kind: str,
    reason: str,
    next_action: str,
    profile_path: str,
    study_id: str = "",
) -> dict[str, str]:
    payload = {
        "kind": kind,
        "reason": reason,
        "next_action": next_action,
        "profile_path": profile_path,
    }
    if study_id:
        payload["study_id"] = study_id
    return payload


def _skipped(reason: str) -> dict[str, Any]:
    return {
        "status": "skipped",
        "can_complete": False,
        "writes_performed": False,
        "reason": reason,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _sequence(value: object) -> list[Any]:
    return list(value) if isinstance(value, list | tuple) else []


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "READ_MODEL",
    "READ_ONLY_CONTRACT",
    "SCHEMA_VERSION",
    "SURFACE",
    "build_paper_autonomy_stability_evidence",
]
