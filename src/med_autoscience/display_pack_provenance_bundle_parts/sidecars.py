from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .refs import PROVENANCE_BUNDLE_REF_PREFIX, _safe_figure_dir, _write_json


def _issues_for_section(bundle: Mapping[str, Any], section_name: str) -> list[dict[str, Any]]:
    return [
        dict(item)
        for item in bundle.get("typed_issues", [])
        if isinstance(item, Mapping) and str(item.get("section") or "") in {section_name, "restricted_refs"}
    ]


def _section_manifest(bundle: Mapping[str, Any], *, section_name: str) -> dict[str, Any]:
    metadata = bundle.get("metadata")
    section_payload = metadata.get(section_name) if isinstance(metadata, Mapping) else {}
    if not isinstance(section_payload, Mapping):
        section_payload = {}
    return {
        "schema_version": 1,
        "bundle_id": str(bundle.get("bundle_id") or ""),
        "figure_id": str(metadata.get("figure_id") or "") if isinstance(metadata, Mapping) else "",
        "section": section_name,
        "refs_only": True,
        "body_embedded": False,
        "status": "pass" if not _issues_for_section(bundle, section_name) else "issues_present",
        "refs": list(section_payload.get("refs") or []),
        "typed_issues": _issues_for_section(bundle, section_name),
        "metadata": {
            key: value
            for key, value in section_payload.items()
            if key not in {"refs", "polish_lifecycle_events", "workflow_figure"}
        },
    }


def _bundle_physical_refs(*, figure_id: str) -> dict[str, str]:
    base = f"{PROVENANCE_BUNDLE_REF_PREFIX}/{_safe_figure_dir(figure_id)}"
    return {
        "bundle": f"{base}/bundle.json",
        "readme": f"{base}/README.md",
        "ro_crate": f"{base}/ro-crate-metadata.json",
        "code_refs": f"{base}/code_refs.json",
        "inputs_manifest": f"{base}/inputs/manifest.json",
        "outputs_manifest": f"{base}/outputs/manifest.json",
        "environment_manifest": f"{base}/environment/manifest.json",
        "agent_trace_manifest": f"{base}/agent_trace/manifest.json",
        "reviews_manifest": f"{base}/reviews/manifest.json",
        "replay_manifest": f"{base}/replay/manifest.json",
    }


def _write_bundle_sidecars(*, bundle_dir: Path, bundle: Mapping[str, Any]) -> dict[str, str]:
    metadata = bundle.get("metadata")
    figure_id = str(metadata.get("figure_id") or "") if isinstance(metadata, Mapping) else ""
    physical_refs = _bundle_physical_refs(figure_id=figure_id)
    replay = metadata.get("replay") if isinstance(metadata, Mapping) else {}
    issue_codes = sorted(
        {
            str(item.get("code") or "")
            for item in bundle.get("typed_issues", [])
            if isinstance(item, Mapping) and item.get("code")
        }
    )
    readme = "\n".join(
        (
            f"# Display Pack figure provenance bundle: {figure_id}",
            "",
            "This directory is a refs-only provenance bundle for one MAS Display Pack figure.",
            "It records locators, hashes, replay readback status, and typed issue codes.",
            "It does not embed figure, input, transcript, or review artifact bodies.",
            "",
            f"- bundle_id: {bundle.get('bundle_id')}",
            f"- artifact_ref: {bundle.get('artifact_ref')}",
            f"- replay_status: {replay.get('status') if isinstance(replay, Mapping) else ''}",
            f"- typed_issue_codes: {', '.join(issue_codes) if issue_codes else 'none'}",
            "",
        )
    )
    (bundle_dir / "README.md").write_text(readme, encoding="utf-8")
    _write_json(
        bundle_dir / "ro-crate-metadata.json",
        {
            "@context": "https://w3id.org/ro/crate/1.1/context",
            "@graph": [
                {
                    "@id": "./",
                    "@type": "Dataset",
                    "name": f"MAS Display Pack figure provenance bundle {figure_id}",
                    "hasPart": [{"@id": Path(ref).name} for ref in physical_refs.values()],
                },
                {
                    "@id": "bundle.json",
                    "@type": "File",
                    "encodingFormat": "application/json",
                    "about": {"@id": str(bundle.get("artifact_ref") or "")},
                },
            ],
            "refs_only": True,
            "authority_boundary": dict(bundle.get("authority_boundary") or {}),
        },
    )
    _write_json(bundle_dir / "code_refs.json", _section_manifest(bundle, section_name="code"))
    for directory_name, section_name in (
        ("inputs", "input"),
        ("outputs", "output"),
        ("environment", "environment"),
        ("agent_trace", "agent_trace"),
        ("reviews", "reviews"),
        ("replay", "replay"),
    ):
        _write_json(
            bundle_dir / directory_name / "manifest.json",
            _section_manifest(bundle, section_name=section_name),
        )
    return physical_refs


def _with_provenance_backrefs(
    payload: Mapping[str, Any] | None,
    *,
    bundle_entries: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if payload is None:
        return None
    updated = dict(payload)
    figures = updated.get("figures")
    if not isinstance(figures, list):
        return updated
    entries_by_id = {str(item.get("figure_id") or ""): item for item in bundle_entries}
    updated_figures: list[Any] = []
    for figure in figures:
        if not isinstance(figure, Mapping):
            updated_figures.append(figure)
            continue
        figure_id = str(figure.get("figure_id") or "")
        bundle_entry = entries_by_id.get(figure_id)
        if bundle_entry is None:
            updated_figures.append(dict(figure))
            continue
        updated_figures.append(
            {
                **dict(figure),
                "provenance_bundle_ref": str(bundle_entry["provenance_bundle_ref"]),
                "provenance_bundle_hash": str(bundle_entry["provenance_bundle_hash"]),
                "provenance_readback_ref": str(bundle_entry["provenance_readback_ref"]),
                "provenance_typed_issue_codes": list(bundle_entry.get("typed_issue_codes") or []),
            }
        )
    updated["figures"] = updated_figures
    return updated


def _write_backref_payloads(
    *,
    paper_root: Path,
    publication_manifest: Mapping[str, Any] | None,
    render_receipt: Mapping[str, Any] | None,
    bundle_entries: list[dict[str, Any]],
) -> None:
    patched_manifest = _with_provenance_backrefs(publication_manifest, bundle_entries=bundle_entries)
    if patched_manifest is not None:
        _write_json(paper_root / "build" / "display_pack_publication_manifest.json", patched_manifest)
    patched_receipt = _with_provenance_backrefs(render_receipt, bundle_entries=bundle_entries)
    if patched_receipt is not None:
        _write_json(paper_root / "figure_render_receipt.json", patched_receipt)
