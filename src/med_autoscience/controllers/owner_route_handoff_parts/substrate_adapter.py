from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Mapping

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol.layout import build_workspace_runtime_layout_for_profile


def build_opl_substrate_adapter_projection(
    *,
    profile: WorkspaceProfile,
    studies: list[Mapping[str, Any]],
    authority_boundary_payload: Callable[[], Mapping[str, Any]],
    workspace_relative: Callable[[Path], str],
    text: Callable[[object], str | None],
    mapping: Callable[[object], Mapping[str, Any]],
) -> dict[str, Any]:
    authority = authority_boundary_payload()
    return {
        "surface_kind": "mas_opl_generic_substrate_adapter",
        "version": "mas-opl-generic-substrate-adapter.v1",
        "target_domain_id": "medautoscience",
        "mode": "opaque_index_only_refs",
        "consumer": "one-person-lab",
        "export_owner": "med-autoscience",
        "workspace_refs": _workspace_substrate_refs(profile=profile),
        "source_refs": _study_substrate_source_refs(profile=profile, studies=studies, text=text),
        "artifact_refs": _study_substrate_artifact_refs(
            profile=profile,
            studies=studies,
            workspace_relative=workspace_relative,
            text=text,
        ),
        "memory_refs": _memory_substrate_refs(
            profile=profile,
            studies=studies,
            text=text,
            mapping=mapping,
        ),
        "projection_policy": {
            "body_included": False,
            "opl_may_index": True,
            "opl_may_resolve_locator": True,
            "opl_may_manage_lifecycle": True,
            "opl_may_project_status": True,
            "opl_may_write_mas_truth": False,
            "opl_may_write_memory_body": False,
            "opl_may_write_evidence_ledger": False,
            "opl_may_write_review_ledger": False,
            "opl_may_write_publication_or_artifact_authority": False,
        },
        "authority_boundary": {
            "mas_owns": [
                "study_truth",
                "memory_body",
                "evidence_ledger",
                "review_ledger",
                "publication_authority",
                "artifact_authority",
            ],
            "opl_owns": ["locator", "index", "lifecycle", "projection"],
            "can_write_domain_truth": False,
            "can_write_memory_body": False,
            "can_write_evidence_ledger": False,
            "can_write_review_ledger": False,
            "can_write_publication_eval": False,
            "can_write_controller_decisions": False,
            "can_write_current_package": False,
            "can_authorize_publication_quality": False,
            "forbidden_authorities": list(authority["forbidden_authorities"]),
        },
    }


def _opaque_ref(
    *,
    role: str,
    ref: str | Path,
    ref_kind: str = "workspace_path",
    exists: bool | None = None,
    study_id: str | None = None,
) -> dict[str, Any]:
    path = ref if isinstance(ref, Path) else None
    payload: dict[str, Any] = {
        "ref_kind": ref_kind,
        "role": role,
        "ref": str(ref),
        "body_included": False,
        "write_permitted": False,
        "opaque_to_opl": True,
        "index_only": True,
    }
    if exists is not None:
        payload["exists"] = bool(exists)
    elif path is not None:
        payload["exists"] = path.exists()
    if study_id is not None:
        payload["study_id"] = study_id
    return payload


def _workspace_substrate_refs(*, profile: WorkspaceProfile) -> list[dict[str, Any]]:
    runtime_artifacts_root = build_workspace_runtime_layout_for_profile(profile).runtime_artifacts_root
    return [
        _opaque_ref(role="workspace_root", ref=profile.workspace_root),
        _opaque_ref(role="runtime_root", ref=profile.runtime_root),
        _opaque_ref(role="studies_root", ref=profile.studies_root),
        _opaque_ref(role="portfolio_root", ref=profile.portfolio_root),
        _opaque_ref(
            role="domain_authority_refs_index",
            ref=runtime_artifacts_root / "domain_authority_refs.sqlite",
        ),
        _opaque_ref(
            role="domain_handler_dispatch_receipt_root",
            ref=runtime_artifacts_root / "opl_family_domain_handler" / "dispatch_receipts",
        ),
    ]


def _study_substrate_source_refs(
    *,
    profile: WorkspaceProfile,
    studies: list[Mapping[str, Any]],
    text: Callable[[object], str | None],
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for study in studies:
        study_id = text(study.get("study_id"))
        if study_id is None:
            continue
        refs.append(_opaque_ref(role="study_root", ref=profile.studies_root / study_id, study_id=study_id))
        for source_ref in study.get("domain_owned_source_refs") or []:
            if not isinstance(source_ref, Mapping):
                continue
            role = text(source_ref.get("role"))
            ref = text(source_ref.get("ref"))
            if role is None or ref is None:
                continue
            refs.append(
                _opaque_ref(
                    role=role,
                    ref=ref,
                    ref_kind=text(source_ref.get("ref_kind")) or "workspace_path",
                    exists=source_ref.get("exists") is True,
                    study_id=study_id,
                )
            )
    return refs


def _study_substrate_artifact_refs(
    *,
    profile: WorkspaceProfile,
    studies: list[Mapping[str, Any]],
    workspace_relative: Callable[[Path], str],
    text: Callable[[object], str | None],
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    artifact_paths = (
        ("publication_eval", Path("artifacts/publication_eval/latest.json")),
        ("controller_decisions", Path("artifacts/controller_decisions/latest.json")),
        ("evidence_ledger", Path("paper/evidence/evidence_ledger.json")),
        ("review_ledger", Path("paper/review/review_ledger.json")),
        ("current_package_root", Path("manuscript/current_package")),
        ("current_package_zip", Path("manuscript/current_package.zip")),
        ("stage_review_index", Path("artifacts/stage_reviews/index.json")),
    )
    for study in studies:
        study_id = text(study.get("study_id"))
        if study_id is None:
            continue
        study_root = profile.studies_root / study_id
        for role, relative_path in artifact_paths:
            refs.append(
                _opaque_ref(
                    role=role,
                    ref=workspace_relative(study_root / relative_path),
                    ref_kind="workspace_relative_path",
                    exists=(study_root / relative_path).exists(),
                    study_id=study_id,
                )
            )
    return refs


def _memory_substrate_refs(
    *,
    profile: WorkspaceProfile,
    studies: list[Mapping[str, Any]],
    text: Callable[[object], str | None],
    mapping: Callable[[object], Mapping[str, Any]],
) -> list[dict[str, Any]]:
    route_memory_root = profile.portfolio_root / "research_memory" / "publication_route_memory"
    refs = [
        _opaque_ref(role="publication_route_memory_pack", ref=route_memory_root / "memory_pack.json"),
        _opaque_ref(role="publication_route_memory_migration_receipt_root", ref=route_memory_root / "migration_receipts"),
        _opaque_ref(role="publication_route_memory_writeback_receipt_root", ref=route_memory_root / "writeback_receipts"),
        _opaque_ref(
            role="domain_memory_descriptor",
            ref="/product_entry_manifest/domain_memory_descriptor",
            ref_kind="json_pointer",
            exists=True,
        ),
    ]
    for study in studies:
        study_id = text(study.get("study_id"))
        proof = mapping(study.get("memory_paper_soak_proof"))
        proof_ref = text(proof.get("proof_ref"))
        if study_id is None or proof_ref is None:
            continue
        refs.append(
            _opaque_ref(
                role="paper_soak_memory_apply_proof",
                ref=proof_ref,
                ref_kind="workspace_relative_path",
                exists=proof.get("status") != "missing",
                study_id=study_id,
            )
        )
        for receipt_ref in proof.get("receipt_refs") or []:
            if not isinstance(receipt_ref, Mapping):
                continue
            ref = text(receipt_ref.get("ref"))
            if ref is None:
                continue
            refs.append(
                _opaque_ref(
                    role=text(receipt_ref.get("ref_kind")) or "memory_receipt_ref",
                    ref=ref,
                    ref_kind="workspace_relative_path",
                    exists=True,
                    study_id=study_id,
                )
            )
    return refs


__all__ = ["build_opl_substrate_adapter_projection"]
