from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.control_plane_migration_audit import (
    build_delivery_manifest_historical_backfill_plan,
    summarize_delivery_manifests,
)
from med_autoscience.controllers.control_plane_route_gate import authorize_control_plane_route


SCHEMA_VERSION = 1
CONTRACT_NAME = "control_plane_backfill_apply.json"
SURFACE = "control_plane_backfill_apply"


def run_backfill_apply(
    *,
    workspace_roots: Iterable[str | Path],
    apply: bool = False,
    control_plane_snapshot: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    route_gate = _route_gate(apply=apply, control_plane_snapshot=control_plane_snapshot)
    workspaces: list[dict[str, Any]] = []
    apply_plan: list[dict[str, Any]] = []
    applied_actions: list[dict[str, Any]] = []
    for workspace_root in sorted(Path(root).expanduser().resolve() for root in workspace_roots):
        workspace = _workspace_plan(workspace_root=workspace_root, route_gate=route_gate)
        workspaces.append(workspace["workspace"])
        for action in workspace["actions"]:
            planned = dict(action)
            if apply and planned["eligible_for_apply"]:
                applied = _apply_backfill_action(planned)
                planned["applied"] = applied["applied"]
                planned["apply_result"] = applied
                if applied["applied"]:
                    applied_actions.append(planned)
            apply_plan.append(planned)

    blocked_count = sum(1 for action in apply_plan if action["blockers"])
    planned_count = sum(1 for action in apply_plan if action["eligible_for_apply"])
    applied_count = len(applied_actions)
    return {
        "surface": SURFACE,
        "schema_version": SCHEMA_VERSION,
        "apply": bool(apply),
        "status": _status(
            applied_count=applied_count,
            blocked_count=blocked_count,
            plan_count=len(apply_plan),
            contract_count=sum(1 for workspace in workspaces if workspace["contract_present"]),
        ),
        "workspace_count": len(workspaces),
        "control_plane_route_action": "delivery_sync",
        "control_plane_route_gate": route_gate,
        "mutation_policy": {
            "default_read_only": True,
            "writes_workspace": bool(applied_count),
            "manual_patch_current_package_allowed": False,
            "manual_patch_submission_minimal_allowed": False,
            "allowed_surfaces": [
                "delivery_manifest.artifact_lifecycle",
                "delivery_manifest.source_signature",
                "delivery_manifest.publication_refs",
            ],
        },
        "action_counts": {
            "planned": planned_count,
            "blocked": blocked_count,
            "applied": applied_count,
            "mutating": applied_count,
        },
        "workspaces": workspaces,
        "apply_plan": apply_plan,
        "applied_actions": applied_actions,
    }


def _route_gate(
    *,
    apply: bool,
    control_plane_snapshot: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if apply:
        return authorize_control_plane_route(
            "delivery_sync",
            {"control_plane_snapshot": dict(control_plane_snapshot or {})},
        )
    gate = authorize_control_plane_route("delivery_sync", {"projection_only": True})
    return {
        **gate,
        "authorized": True,
        "allowed": True,
        "blocking_reasons": [],
        "planning_only": True,
    }


def _workspace_plan(*, workspace_root: Path, route_gate: Mapping[str, Any]) -> dict[str, Any]:
    contract_path = workspace_root / CONTRACT_NAME
    contract = _read_json(contract_path)
    contract_actions = _contract_actions(contract)
    delivery_manifest_paths = _delivery_manifest_paths(workspace_root)
    actions = [
        _plan_backfill_action(
            workspace_root=workspace_root,
            contract_path=contract_path,
            contract=contract,
            contract_actions=contract_actions,
            route_gate=route_gate,
            manifest_path=manifest_path,
        )
        for manifest_path in delivery_manifest_paths
    ]
    return {
        "workspace": {
            "workspace_root": str(workspace_root),
            "contract_path": str(contract_path),
            "contract_present": contract_path.exists(),
            "delivery_manifest_count": len(delivery_manifest_paths),
            "action_count": len(actions),
        },
        "actions": actions,
    }


def _plan_backfill_action(
    *,
    workspace_root: Path,
    contract_path: Path,
    contract: Mapping[str, Any],
    contract_actions: set[str],
    route_gate: Mapping[str, Any],
    manifest_path: Path,
) -> dict[str, Any]:
    payload = _read_json(manifest_path)
    summary = summarize_delivery_manifests([manifest_path])
    historical_plan = build_delivery_manifest_historical_backfill_plan(summary)
    missing_surfaces = list(historical_plan.get("missing_surfaces") or []) if historical_plan else []
    actions = _actions_for_missing_surfaces(missing_surfaces)
    blockers = _dedupe(
        [
            *_route_gate_blockers(route_gate),
            *_contract_blockers(contract_path=contract_path, contract=contract, required_actions=actions),
            *_target_blockers(workspace_root=workspace_root, manifest_path=manifest_path),
        ]
    )
    if not actions:
        blockers.append("no_backfill_required")
    return {
        "workspace_root": str(workspace_root),
        "delivery_manifest_path": str(manifest_path),
        "workspace_relative_path": _rel(manifest_path, workspace_root),
        "actions": actions,
        "missing_surfaces": missing_surfaces,
        "eligible_for_apply": bool(actions) and not blockers,
        "blockers": blockers,
        "control_plane_route_gate": dict(route_gate),
        "controller_contract_ref": str(contract_path),
        "historical_backfill_plan": dict(historical_plan or {}),
        "patch_preview": _patch_preview(
            manifest_path=manifest_path,
            payload=payload,
            missing_surfaces=missing_surfaces,
        ),
        "applied": False,
    }


def _actions_for_missing_surfaces(missing_surfaces: Iterable[str]) -> list[str]:
    actions: list[str] = []
    for surface in missing_surfaces:
        if surface == "delivery_manifest_lifecycle_hook":
            actions.append("backfill_delivery_manifest_lifecycle_hook")
        elif surface == "source_signature":
            actions.append("backfill_delivery_manifest_source_signature")
        elif surface == "publication_refs":
            actions.append("backfill_delivery_manifest_publication_refs")
    return actions


def _patch_preview(*, manifest_path: Path, payload: Mapping[str, Any], missing_surfaces: list[str]) -> dict[str, Any]:
    return {
        "will_write_delivery_manifest": bool(missing_surfaces),
        "will_touch_current_package": False,
        "will_touch_submission_minimal": False,
        "field_paths": _field_paths_for_missing_surfaces(missing_surfaces),
        "source_signature": _delivery_source_signature(manifest_path=manifest_path, payload=payload),
        "publication_refs": _publication_refs(manifest_path=manifest_path),
    }


def _field_paths_for_missing_surfaces(missing_surfaces: Iterable[str]) -> list[str]:
    paths: list[str] = []
    for surface in missing_surfaces:
        if surface == "delivery_manifest_lifecycle_hook":
            paths.append("artifact_lifecycle")
        elif surface == "source_signature":
            paths.extend(["source_signature", "authority_source_signature"])
        elif surface == "publication_refs":
            paths.append("publication_refs")
    return paths


def _apply_backfill_action(action: Mapping[str, Any]) -> dict[str, Any]:
    manifest_path = Path(str(action["delivery_manifest_path"]))
    payload = dict(_read_json(manifest_path))
    missing_surfaces = [str(item) for item in action.get("missing_surfaces") or []]
    if "delivery_manifest_lifecycle_hook" in missing_surfaces:
        payload["artifact_lifecycle"] = _lifecycle_hook(manifest_path)
    if "source_signature" in missing_surfaces:
        signature = _delivery_source_signature(manifest_path=manifest_path, payload=payload)
        payload["source_signature"] = signature
        payload["authority_source_signature"] = signature
    if "publication_refs" in missing_surfaces:
        payload["publication_refs"] = _publication_refs(manifest_path=manifest_path)
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "applied": True,
        "delivery_manifest_path": str(manifest_path),
        "field_paths": _field_paths_for_missing_surfaces(missing_surfaces),
    }


def _lifecycle_hook(manifest_path: Path) -> dict[str, Any]:
    study_root = _study_root_for_manifest(manifest_path)
    return {
        "authority_sync": {
            "source": "control_plane_backfill_apply",
            "manual_patch_allowed": False,
        },
        "lifecycle_roles": {
            "current_package": "derived_projection",
            "submission_minimal": "human_handoff_mirror",
            "delivery_manifest": "audit_log",
        },
        "source_refs": {
            "study_root": str(study_root),
            "canonical_regeneration_path": "refresh_canonical_manuscript_sources",
        },
    }


def _publication_refs(*, manifest_path: Path) -> dict[str, Any]:
    study_root = _study_root_for_manifest(manifest_path)
    return {
        "publication_gate": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        "paper_bundle_manifest": str(study_root / "paper" / "paper_bundle_manifest.json"),
        "submission_minimal_manifest": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
    }


def _delivery_source_signature(*, manifest_path: Path, payload: Mapping[str, Any]) -> str:
    study_root = _study_root_for_manifest(manifest_path)
    source_parts = {
        "surface": payload.get("surface") or "delivery_manifest",
        "study_id": payload.get("study_id") or study_root.name,
        "study_root": str(study_root),
        "current_package": str(study_root / "manuscript" / "current_package"),
        "submission_minimal": str(study_root / "paper" / "submission_minimal"),
    }
    encoded = json.dumps(source_parts, sort_keys=True, separators=(",", ":"))
    return f"delivery-source::{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:24]}"


def _contract_blockers(
    *,
    contract_path: Path,
    contract: Mapping[str, Any],
    required_actions: Iterable[str],
) -> list[str]:
    if not contract_path.exists():
        return ["backfill_apply_contract_missing"]
    controller_decision = _mapping(contract.get("controller_decision"))
    if (
        controller_decision.get("apply_intent") is not True
        or _text(controller_decision.get("decision")) != "approve_backfill_apply"
    ):
        return ["controller_backfill_apply_intent_missing"]
    allowlist = set(_string_list(contract.get("action_allowlist")))
    missing = [action for action in required_actions if action not in allowlist]
    return [f"action_not_allowlisted:{action}" for action in missing]


def _route_gate_blockers(route_gate: Mapping[str, Any]) -> list[str]:
    if bool(route_gate.get("authorized")):
        return []
    return [
        f"control_plane_route_gate:{reason}"
        for reason in _string_list(route_gate.get("blocking_reasons"))
    ]


def _target_blockers(*, workspace_root: Path, manifest_path: Path) -> list[str]:
    try:
        manifest_path.resolve().relative_to(workspace_root.resolve())
    except ValueError:
        return ["target_outside_workspace"]
    if manifest_path.name != "delivery_manifest.json":
        return ["target_not_delivery_manifest"]
    return []


def _status(*, applied_count: int, blocked_count: int, plan_count: int, contract_count: int) -> str:
    if applied_count:
        return "applied"
    if blocked_count:
        return "blocked"
    if plan_count:
        return "planned"
    if contract_count == 0:
        return "no_contract"
    return "no_backfill_required"


def _delivery_manifest_paths(workspace_root: Path) -> list[Path]:
    if not workspace_root.exists():
        return []
    return sorted(
        path
        for path in workspace_root.rglob("delivery_manifest.json")
        if ".git" not in path.parts and ".ds" not in path.parts
    )


def _contract_actions(contract: Mapping[str, Any]) -> set[str]:
    return set(_string_list(contract.get("action_allowlist")))


def _read_json(path: Path) -> Mapping[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, Mapping) else {}


def _study_root_for_manifest(manifest_path: Path) -> Path:
    candidate = manifest_path.parent
    while candidate.name in {"manuscript", "current_package", "paper", "submission_minimal"}:
        candidate = candidate.parent
    return candidate


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _dedupe(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


__all__ = ["SCHEMA_VERSION", "SURFACE", "run_backfill_apply"]
