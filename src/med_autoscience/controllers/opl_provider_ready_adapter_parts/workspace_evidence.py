from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol.layout import build_workspace_runtime_layout_for_profile

from .provider_readiness import DOMAIN_OWNER, TARGET_DOMAIN_ID


def build_workspace_runtime_evidence_receipt_surface(*, profile: WorkspaceProfile) -> dict[str, Any]:
    observed_refs = _workspace_root_refs(profile)
    observed_refs.extend(_study_refs(profile))
    observed_refs.extend(_portfolio_refs(profile))
    owner_receipt_refs = [
        ref["ref"]
        for ref in observed_refs
        if ref["exists"] is True and ref["role"] in {"owner_route_receipt", "guarded_apply_receipt"}
    ]
    status = "workspace_runtime_evidence_refs_observed" if owner_receipt_refs else "typed_blocker"
    return {
        "surface_kind": "mas_workspace_runtime_evidence_receipt",
        "version": "mas-workspace-runtime-evidence-receipt.v1",
        "target_domain_id": TARGET_DOMAIN_ID,
        "owner": DOMAIN_OWNER,
        "mode": "body_free_refs_only",
        "status": status,
        "workspace_root": str(profile.workspace_root),
        "runtime_root": str(profile.runtime_root),
        "studies_root": str(profile.studies_root),
        "locator_ref": "/product_entry_manifest/workspace_runtime_artifact_root_locator",
        "observed_ref_count": sum(1 for ref in observed_refs if ref["exists"] is True),
        "observed_refs": observed_refs,
        "owner_receipt_refs": owner_receipt_refs,
        "typed_blocker": None
        if owner_receipt_refs
        else {
            "surface_kind": "mas_workspace_runtime_evidence_typed_blocker",
            "blocker_id": "mas_live_workspace_runtime_owner_receipt_missing",
            "owner": DOMAIN_OWNER,
            "reason": (
                "No MAS owner route or guarded-apply receipt was observed in the workspace/runtime "
                "artifact locators. MAS can expose body-free refs, but paper progress still requires "
                "a MAS owner receipt or a live gate typed blocker."
            ),
            "required_owner_surface": "MAS owner route receipt or guarded apply receipt",
            "write_permitted": False,
        },
        "live_apply_claims": {
            "provider_hosted_live_apply_claimed": False,
            "long_soak_claimed": False,
            "publication_closure_claimed": False,
            "paper_progress_requires_mas_owner_receipt": True,
        },
        "authority_boundary": {
            "proof_owner": DOMAIN_OWNER,
            "domain_truth_owner": DOMAIN_OWNER,
            "read_only": True,
            "body_included": False,
            "can_write_domain_truth": False,
            "can_write_artifact_body": False,
            "can_write_memory_body": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
        },
    }


def _workspace_root_refs(profile: WorkspaceProfile) -> list[dict[str, Any]]:
    runtime_artifacts_root = build_workspace_runtime_layout_for_profile(profile).runtime_artifacts_root
    return [
        _ref("workspace_root", profile.workspace_root),
        _ref("runtime_root", profile.runtime_root),
        _ref("studies_root", profile.studies_root),
        _ref(
            "domain_handler_dispatch_receipt_root",
            runtime_artifacts_root / "opl_family_domain_handler" / "dispatch_receipts",
        ),
        _ref(
            "domain_authority_refs_index",
            runtime_artifacts_root / "domain_authority_refs.sqlite",
        ),
    ]


def _study_refs(profile: WorkspaceProfile) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for study_root in _study_roots(profile.studies_root):
        refs.extend(
            [
                _ref("study_root", study_root, study_id=study_root.name),
                _ref("owner_route_receipt", study_root / "artifacts" / "runtime" / "owner_route" / "latest.json", study_id=study_root.name),
                _ref("stage_review_index", study_root / "artifacts" / "stage_reviews" / "index.json", study_id=study_root.name),
                _ref("publication_eval", study_root / "artifacts" / "publication_eval" / "latest.json", study_id=study_root.name),
                _ref("controller_decisions", study_root / "artifacts" / "controller_decisions" / "latest.json", study_id=study_root.name),
                _ref("domain_health_diagnostic", study_root / "artifacts" / "domain_health_diagnostic" / "latest.json", study_id=study_root.name),
            ]
        )
        refs.extend(
            _ref("guarded_apply_receipt", path, study_id=study_root.name)
            for path in sorted((study_root / "artifacts" / "autonomy" / "guarded_apply").glob("*.json"))
        )
    return refs


def _portfolio_refs(profile: WorkspaceProfile) -> list[dict[str, Any]]:
    route_memory_root = profile.portfolio_root / "research_memory" / "publication_route_memory"
    return [
        _ref("publication_route_memory_pack", route_memory_root / "memory_pack.json"),
        _ref("publication_route_memory_migration_receipt_root", route_memory_root / "migration_receipts"),
        _ref("publication_route_memory_writeback_receipt_root", route_memory_root / "writeback_receipts"),
    ]


def _study_roots(studies_root: Path) -> list[Path]:
    if not studies_root.exists():
        return []
    return sorted(path for path in studies_root.iterdir() if path.is_dir())


def _ref(role: str, path: Path, *, study_id: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "ref_kind": "workspace_path",
        "role": role,
        "ref": str(path),
        "exists": path.exists(),
        "body_included": False,
        "write_permitted": False,
    }
    if study_id is not None:
        payload["study_id"] = study_id
    return payload


__all__ = ["build_workspace_runtime_evidence_receipt_surface"]
