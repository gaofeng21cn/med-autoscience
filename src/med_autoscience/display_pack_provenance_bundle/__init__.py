from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .bundle_assembly import _build_bundle
from .refs import (
    PUBLICATION_MANIFEST_REF,
    PROVENANCE_BUNDLE_REF_PREFIX,
    PROVENANCE_INDEX_REF,
    _figures_by_id,
    _read_json_object,
    _resolve_ref_path,
    _safe_figure_dir,
    _sha256_file,
    _utc_now,
    _write_json,
)
from .sidecars import (
    _write_backref_payloads,
    _write_bundle_sidecars,
)


def materialize_figure_provenance_bundles(
    *,
    repo_root: Path | str,
    paper_root: Path | str,
) -> dict[str, Any]:
    normalized_repo_root = Path(repo_root).expanduser().resolve()
    normalized_paper_root = Path(paper_root).expanduser().resolve()
    publication_manifest = _read_json_object(normalized_paper_root / "build" / "display_pack_publication_manifest.json")
    display_pack_lock = _read_json_object(normalized_paper_root / "build" / "display_pack_lock.json")
    render_receipt = _read_json_object(normalized_paper_root / "figure_render_receipt.json")
    visual_audit_receipt = _read_json_object(normalized_paper_root / "figure_visual_audit_receipt.json")
    polish_lifecycle = _read_json_object(normalized_paper_root / "figure_polish_lifecycle.json")
    workflow_packet = _read_json_object(normalized_paper_root / "figure_workflow_packet.json")
    agent_trace_refs = _read_json_object(normalized_paper_root / "build" / "provenance" / "agent_trace_refs.json")

    figure_ids = sorted({
        *_figures_by_id(publication_manifest).keys(),
        *_figures_by_id(render_receipt).keys(),
    })
    bundles = []
    for figure_id in figure_ids:
        bundle = _build_bundle(
            figure_id=figure_id,
            repo_root=normalized_repo_root,
            paper_root=normalized_paper_root,
            publication_manifest=publication_manifest,
            display_pack_lock=display_pack_lock,
            render_receipt=render_receipt,
            visual_audit_receipt=visual_audit_receipt,
            polish_lifecycle=polish_lifecycle,
            workflow_packet=workflow_packet,
            agent_trace_refs=agent_trace_refs,
        )
        bundle_ref = f"{PROVENANCE_BUNDLE_REF_PREFIX}/{_safe_figure_dir(figure_id)}/bundle.json"
        bundle_path = _resolve_ref_path(bundle_ref, paper_root=normalized_paper_root)
        _write_json(bundle_path, bundle)
        physical_refs = _write_bundle_sidecars(bundle_dir=bundle_path.parent, bundle=bundle)
        typed_issue_codes = sorted(
            {
                str(item.get("code") or "")
                for item in bundle.get("typed_issues", [])
                if isinstance(item, Mapping) and item.get("code")
            }
        )
        replay_status = str(bundle.get("metadata", {}).get("replay", {}).get("status") or "")
        bundles.append(
            {
                "figure_id": figure_id,
                "provenance_bundle_ref": bundle_ref,
                "provenance_bundle_hash": _sha256_file(bundle_path),
                "provenance_readback_ref": physical_refs["replay_manifest"],
                "physical_bundle_refs": physical_refs,
                "replay_status": replay_status,
                "missing_ref_count": len(bundle["missing_refs"]),
                "restricted_ref_count": len(bundle["restricted_refs"]),
                "typed_issue_count": len(bundle["typed_issues"]),
                "typed_issue_codes": typed_issue_codes,
                "typed_issues": list(bundle["typed_issues"]),
            }
        )

    index = {
        "schema_version": 1,
        "surface_kind": "display_pack_figure_provenance_index",
        "status": "materialized" if bundles else "no_figures",
        "created_at": _utc_now(),
        "repo_root": str(normalized_repo_root),
        "paper_root": str(normalized_paper_root),
        "publication_manifest_ref": PUBLICATION_MANIFEST_REF,
        "bundle_count": len(bundles),
        "bundles": bundles,
        "authority_boundary": {
            "index_is_projection_from_bundle_files": True,
            "can_authorize_publication_readiness": False,
            "can_authorize_quality_verdict": False,
            "can_mutate_data_or_statistics": False,
            "can_replace_owner_receipt": False,
        },
    }
    index_path = _resolve_ref_path(PROVENANCE_INDEX_REF, paper_root=normalized_paper_root)
    _write_json(index_path, index)
    _write_backref_payloads(
        paper_root=normalized_paper_root,
        publication_manifest=publication_manifest,
        render_receipt=render_receipt,
        bundle_entries=bundles,
    )
    return {
        **index,
        "path": str(index_path),
        "ref": PROVENANCE_INDEX_REF,
        "sha256": _sha256_file(index_path),
    }


__all__ = [
    "PROVENANCE_INDEX_REF",
    "materialize_figure_provenance_bundles",
]
