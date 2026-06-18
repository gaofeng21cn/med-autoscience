from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping


OPL_STORAGE_MAINTENANCE_AUTHORIZATION_SURFACE_KIND = "opl_runtime_storage_maintenance_authorization"
AUTHORIZATION_PROOF_SURFACE_KIND = "opl_runtime_storage_maintenance_authorization_proof"
AUTHORIZATION_BLOCKER_STATUS = "blocked_opl_runtime_storage_maintenance_authorization_required"
AUTHORIZATION_TYPED_BLOCKER = "opl_runtime_storage_maintenance_authorization_required"


def opl_storage_maintenance_authorization_result(
    *,
    apply: bool,
    authorization: Mapping[str, Any] | None,
    operation: str,
    maintenance_surface: str,
    workspace_root: Path | None = None,
    quest_root: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    roots = _root_expectations(workspace_root=workspace_root, quest_root=quest_root)
    base = {
        "surface_kind": AUTHORIZATION_PROOF_SURFACE_KIND,
        "schema_version": 1,
        "status": "not_required_for_dry_run" if not apply else "missing",
        "required_for_apply": bool(apply),
        "generic_maintenance_owner": "one-person-lab",
        "mas_role": "maintenance_callable_adapter",
        "operation": operation,
        "maintenance_surface": maintenance_surface,
        "can_create_opl_command": False,
        "can_create_opl_event": False,
        "can_create_opl_outbox": False,
        "can_claim_runtime_currentness": False,
        "can_claim_paper_progress": False,
        **{field: str(path) for field, path in roots.items()},
    }
    if not apply:
        return base, None
    if not isinstance(authorization, Mapping):
        return base, authorization_blocker(base, reason="missing_authorization")
    proof = dict(base)
    proof["authorization"] = authorization_projection(authorization)
    if authorization.get("surface_kind") != OPL_STORAGE_MAINTENANCE_AUTHORIZATION_SURFACE_KIND:
        proof["status"] = "invalid"
        return proof, authorization_blocker(proof, reason="invalid_surface_kind")
    authorized_operation = str(authorization.get("operation") or "")
    batch_workspace_authorization = (
        operation == "quest_runtime_storage_apply"
        and authorized_operation == "workspace_storage_apply"
        and bool(str(authorization.get("workspace_root") or "").strip())
    )
    if authorized_operation != operation and not batch_workspace_authorization:
        proof["status"] = "invalid"
        return proof, authorization_blocker(proof, reason="operation_mismatch")
    authorized_surface = str(authorization.get("maintenance_surface") or "")
    batch_workspace_surface = (
        maintenance_surface == "quest_runtime_storage_maintenance"
        and authorized_surface == "workspace_runtime_storage_maintenance"
        and batch_workspace_authorization
    )
    if authorized_surface != maintenance_surface and not batch_workspace_surface:
        proof["status"] = "invalid"
        return proof, authorization_blocker(proof, reason="maintenance_surface_mismatch")
    for field, expected_path in roots.items():
        authorized_path = str(authorization.get(field) or "").strip()
        if not authorized_path:
            continue
        if Path(authorized_path).expanduser().resolve() != expected_path:
            proof["status"] = "invalid"
            return proof, authorization_blocker(proof, reason=f"{field}_mismatch")
    if not any(str(authorization.get(field) or "").strip() for field in roots):
        proof["status"] = "invalid"
        root_fields = "_or_".join(roots) or "scope"
        return proof, authorization_blocker(proof, reason=f"missing_{root_fields}")
    outcome = str(authorization.get("outcome") or "").strip()
    if outcome != "authorized":
        proof["status"] = "invalid"
        return proof, authorization_blocker(proof, reason="outcome_not_authorized")
    if not _non_empty_text(authorization.get("authorization_ref")):
        proof["status"] = "invalid"
        return proof, authorization_blocker(proof, reason="missing_authorization_ref")
    proof["status"] = "authorized"
    proof["authorization_ref"] = str(authorization.get("authorization_ref"))
    proof["outcome"] = outcome
    return proof, None


def authorization_projection(authorization: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_kind": authorization.get("surface_kind"),
        "operation": authorization.get("operation"),
        "maintenance_surface": authorization.get("maintenance_surface"),
        "workspace_root": authorization.get("workspace_root"),
        "quest_root": authorization.get("quest_root"),
        "outcome": authorization.get("outcome"),
        "authorization_ref": authorization.get("authorization_ref"),
        "owner": authorization.get("owner"),
        "stage_run_id": authorization.get("stage_run_id"),
        "event_ref": authorization.get("event_ref"),
        "outbox_ref": authorization.get("outbox_ref"),
    }


def authorization_blocker(proof: Mapping[str, Any], *, reason: str) -> dict[str, Any]:
    return {
        "status": AUTHORIZATION_BLOCKER_STATUS,
        "reason": reason,
        "typed_blocker": AUTHORIZATION_TYPED_BLOCKER,
        "stable_blocker": True,
        "owner": "one-person-lab",
        "mas_role": "maintenance_callable_adapter",
        "opl_maintenance_authorization": dict(proof),
    }


def _root_expectations(*, workspace_root: Path | None, quest_root: Path | None) -> dict[str, Path]:
    roots: dict[str, Path] = {}
    if workspace_root is not None:
        roots["workspace_root"] = Path(workspace_root).expanduser().resolve()
    if quest_root is not None:
        roots["quest_root"] = Path(quest_root).expanduser().resolve()
    return roots


def _non_empty_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())
