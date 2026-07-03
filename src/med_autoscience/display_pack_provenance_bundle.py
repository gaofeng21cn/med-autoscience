from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


PROVENANCE_INDEX_REF = "paper/build/provenance/figure_provenance_index.json"
PROVENANCE_BUNDLE_REF_PREFIX = "paper/build/provenance/figures"
PUBLICATION_MANIFEST_REF = "paper/build/display_pack_publication_manifest.json"
DISPLAY_PACK_LOCK_REF = "paper/build/display_pack_lock.json"
FIGURE_RENDER_RECEIPT_REF = "paper/figure_render_receipt.json"
FIGURE_VISUAL_AUDIT_RECEIPT_REF = "paper/figure_visual_audit_receipt.json"
FIGURE_POLISH_LIFECYCLE_REF = "paper/figure_polish_lifecycle.json"
FIGURE_WORKFLOW_PACKET_REF = "paper/figure_workflow_packet.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _safe_figure_dir(figure_id: str) -> str:
    safe = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in figure_id.strip())
    if not safe:
        raise ValueError("figure_id must be non-empty")
    return safe


def _workspace_ref(path: Path, *, paper_root: Path) -> str:
    return path.resolve().relative_to(paper_root.resolve().parent).as_posix()


def _split_ref_pointer(ref: str) -> tuple[str, str]:
    ref_text = str(ref or "").strip()
    if "#" not in ref_text:
        return ref_text, ""
    path_ref, pointer = ref_text.split("#", 1)
    return path_ref, f"#{pointer}"


def _resolve_ref_path(ref: str, *, paper_root: Path) -> Path:
    path_ref, _pointer = _split_ref_pointer(ref)
    path = Path(path_ref).expanduser()
    if path.is_absolute():
        return path.resolve()
    if path.parts and path.parts[0] == paper_root.name:
        return (paper_root.parent / path).resolve()
    return (paper_root / path).resolve()


def _resolve_existing_ref_path(ref: str, *, paper_root: Path, repo_root: Path) -> Path:
    path_ref, _pointer = _split_ref_pointer(ref)
    path = Path(path_ref).expanduser()
    if path.is_absolute():
        return path.resolve()
    paper_candidate = _resolve_ref_path(path_ref, paper_root=paper_root)
    if paper_candidate.exists():
        return paper_candidate
    return (repo_root / path).resolve()


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _file_ref(
    ref: str,
    *,
    paper_root: Path,
    repo_root: Path,
    label: str,
    required: bool = True,
) -> dict[str, Any]:
    path_ref, pointer = _split_ref_pointer(ref)
    resolved = _resolve_existing_ref_path(path_ref, paper_root=paper_root, repo_root=repo_root)
    payload: dict[str, Any] = {
        "label": label,
        "ref": ref,
        "required": required,
    }
    if pointer:
        payload["json_pointer"] = pointer
    if not resolved.exists():
        return {
            **payload,
            "status": "missing",
            "reason": "path_not_found",
        }
    if not (_is_under(resolved, paper_root.parent) or _is_under(resolved, repo_root)):
        return {
            **payload,
            "status": "restricted",
            "restricted_locator": {
                "kind": "absolute_path_outside_paper_or_repo",
                "basename": resolved.name,
                "path_sha256": _sha256_text(str(resolved)),
            },
        }
    return {
        **payload,
        "status": "present",
        "path": str(resolved),
        "sha256": _sha256_file(resolved),
    }


def _ref_from_path(path: str, *, paper_root: Path) -> str:
    if not path:
        return ""
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        try:
            return _workspace_ref(candidate, paper_root=paper_root)
        except ValueError:
            return str(candidate)
    return path


def _list_file_refs(
    refs: list[str],
    *,
    paper_root: Path,
    repo_root: Path,
    label_prefix: str,
    required: bool = True,
) -> list[dict[str, Any]]:
    return [
        _file_ref(ref, paper_root=paper_root, repo_root=repo_root, label=f"{label_prefix}_{index}", required=required)
        for index, ref in enumerate(refs)
        if str(ref or "").strip()
    ]


def _figure_id(item: Mapping[str, Any]) -> str:
    return str(item.get("figure_id") or "").strip()


def _figures_by_id(payload: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    figures = payload.get("figures") if payload is not None else None
    if not isinstance(figures, list):
        return {}
    return {
        figure_id: dict(item)
        for item in figures
        if isinstance(item, Mapping) and (figure_id := _figure_id(item))
    }


def _global_surface_refs() -> list[tuple[str, str]]:
    return [
        ("publication_manifest", PUBLICATION_MANIFEST_REF),
        ("display_pack_lock", DISPLAY_PACK_LOCK_REF),
        ("figure_render_receipt", FIGURE_RENDER_RECEIPT_REF),
        ("figure_visual_audit_receipt", FIGURE_VISUAL_AUDIT_RECEIPT_REF),
        ("figure_polish_lifecycle", FIGURE_POLISH_LIFECYCLE_REF),
        ("figure_workflow_packet", FIGURE_WORKFLOW_PACKET_REF),
    ]


def _template_lock_entry(
    *,
    display_pack_lock: Mapping[str, Any] | None,
    template_id: str,
) -> dict[str, Any]:
    packs = display_pack_lock.get("enabled_packs") if display_pack_lock is not None else []
    if not isinstance(packs, list):
        return {}
    for pack in packs:
        if not isinstance(pack, Mapping):
            continue
        templates = pack.get("templates")
        if not isinstance(templates, list):
            continue
        for template in templates:
            if not isinstance(template, Mapping):
                continue
            if template_id in {
                str(template.get("template_id") or ""),
                str(template.get("full_template_id") or ""),
            }:
                return dict(template)
    return {}


def _renderer_code_ref(
    *,
    render_result: Mapping[str, Any],
    paper_root: Path,
    repo_root: Path,
) -> dict[str, Any] | None:
    argv = render_result.get("argv")
    cwd_text = str(render_result.get("cwd") or "").strip()
    if not isinstance(argv, list) or not cwd_text:
        return None
    cwd = Path(cwd_text).expanduser()
    for token in argv:
        token_text = str(token or "").strip()
        if not token_text or token_text.startswith("-"):
            continue
        candidate = Path(token_text)
        if candidate.suffix not in {".R", ".py"}:
            continue
        resolved = candidate if candidate.is_absolute() else cwd / candidate
        return _file_ref(
            str(resolved),
            paper_root=paper_root,
            repo_root=repo_root,
            label="renderer_entrypoint_file",
            required=True,
        )
    return None


def _bundle_missing_refs(bundle: Mapping[str, Any]) -> list[dict[str, Any]]:
    missing: list[dict[str, Any]] = []
    for section_name in ("source_surfaces", "code", "input", "output", "environment", "reviews", "replay"):
        section = bundle.get(section_name)
        if not isinstance(section, Mapping):
            continue
        refs = section.get("refs")
        if not isinstance(refs, list):
            continue
        missing.extend(
            dict(item)
            for item in refs
            if isinstance(item, Mapping) and item.get("status") == "missing"
        )
    return missing


def _bundle_restricted_refs(bundle: Mapping[str, Any]) -> list[dict[str, Any]]:
    restricted: list[dict[str, Any]] = []
    for section_name in ("source_surfaces", "code", "input", "output", "environment", "reviews", "replay"):
        section = bundle.get(section_name)
        if not isinstance(section, Mapping):
            continue
        refs = section.get("refs")
        if not isinstance(refs, list):
            continue
        restricted.extend(
            dict(item)
            for item in refs
            if isinstance(item, Mapping) and item.get("status") == "restricted"
        )
    return restricted


def _ref_values(refs: list[dict[str, Any]]) -> list[str]:
    values: list[str] = []
    for item in refs:
        ref = str(item.get("ref") or "").strip()
        if ref:
            values.append(ref)
    return values


def _hashes_from_refs(*sections: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    hashes: dict[str, dict[str, str]] = {}
    for refs in sections:
        for item in refs:
            ref = str(item.get("ref") or "").strip()
            digest = str(item.get("sha256") or "").strip()
            if not ref or not digest:
                continue
            key = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in ref)[:160]
            hashes[key or f"ref_{len(hashes)}"] = {"algorithm": "sha256", "value": digest}
    return hashes


def _build_bundle(
    *,
    figure_id: str,
    repo_root: Path,
    paper_root: Path,
    publication_manifest: Mapping[str, Any] | None,
    display_pack_lock: Mapping[str, Any] | None,
    render_receipt: Mapping[str, Any] | None,
    visual_audit_receipt: Mapping[str, Any] | None,
    polish_lifecycle: Mapping[str, Any] | None,
    workflow_packet: Mapping[str, Any] | None,
) -> dict[str, Any]:
    manifest_figures = _figures_by_id(publication_manifest)
    render_figures = _figures_by_id(render_receipt)
    manifest_figure = manifest_figures.get(figure_id, {})
    render_figure = render_figures.get(figure_id, {})
    figure = {**render_figure, **manifest_figure}
    rendered = dict(figure.get("rendered_artifacts") or {})
    render_result = dict(figure.get("render_result") or render_figure.get("render_result") or {})
    template_id = str(figure.get("template_id") or render_figure.get("template_id") or "").strip()
    template_entry = _template_lock_entry(display_pack_lock=display_pack_lock, template_id=template_id)

    source_surface_refs = [
        _file_ref(ref, paper_root=paper_root, repo_root=repo_root, label=label, required=True)
        for label, ref in _global_surface_refs()
    ]
    code_refs = [
        _file_ref(
            str(template_entry.get("template_manifest_path") or ""),
            paper_root=paper_root,
            repo_root=repo_root,
            label="template_manifest",
            required=bool(template_entry),
        )
    ] if template_entry else []
    for key in ("render_script_path", "r_evidence_helper_path", "renderer_dependency_profile_path"):
        value = str(template_entry.get(key) or "").strip()
        if value:
            code_refs.append(_file_ref(value, paper_root=paper_root, repo_root=repo_root, label=key, required=False))
    renderer_code_ref = _renderer_code_ref(render_result=render_result, paper_root=paper_root, repo_root=repo_root)
    if renderer_code_ref is not None:
        code_refs.append(renderer_code_ref)

    data_refs = [str(ref) for ref in render_figure.get("source_data_refs") or []]
    if not data_refs and figure.get("data_ref"):
        data_refs = [str(figure["data_ref"])]
    style_profile = dict(figure.get("publication_style_profile") or {})
    input_refs = _list_file_refs(
        data_refs,
        paper_root=paper_root,
        repo_root=repo_root,
        label_prefix="source_data",
    )
    if style_profile.get("ref"):
        input_refs.append(
            _file_ref(str(style_profile["ref"]), paper_root=paper_root, repo_root=repo_root, label="style_profile")
        )
    if render_result.get("request_ref") or render_result.get("request_path"):
        input_refs.append(
            _file_ref(
                str(render_result.get("request_ref") or _ref_from_path(str(render_result.get("request_path") or ""), paper_root=paper_root)),
                paper_root=paper_root,
                repo_root=repo_root,
                label="render_request",
            )
        )

    output_refs = _list_file_refs(
        [
            str(rendered.get("png_ref") or ""),
            str(rendered.get("pdf_ref") or ""),
            str(rendered.get("layout_sidecar_ref") or ""),
            str(figure.get("deterministic_qc", {}).get("ref") or ""),
            f"paper/build/display_artifact_manifest.{figure_id}.json",
        ],
        paper_root=paper_root,
        repo_root=repo_root,
        label_prefix="rendered_output",
    )

    environment_refs: list[dict[str, Any]] = []
    for key in ("stdout_ref", "stderr_ref"):
        if render_result.get(key):
            environment_refs.append(
                _file_ref(str(render_result[key]), paper_root=paper_root, repo_root=repo_root, label=key, required=False)
            )
    dependency_environment = dict(
        figure.get("dependency_environment")
        or render_figure.get("dependency_environment")
        or (render_receipt or {}).get("dependency_environment")
        or (publication_manifest or {}).get("dependency_environment")
        or {}
    )
    if dependency_environment.get("run_context_ref"):
        environment_refs.append(
            _file_ref(
                str(dependency_environment["run_context_ref"]),
                paper_root=paper_root,
                repo_root=repo_root,
                label="dependency_run_context",
                required=False,
            )
        )

    review_refs = [
        _file_ref(FIGURE_VISUAL_AUDIT_RECEIPT_REF, paper_root=paper_root, repo_root=repo_root, label="visual_audit")
    ]
    replay_refs = []
    if render_result.get("request_ref") or render_result.get("request_path"):
        replay_refs.append(
            _file_ref(
                str(render_result.get("request_ref") or _ref_from_path(str(render_result.get("request_path") or ""), paper_root=paper_root)),
                paper_root=paper_root,
                repo_root=repo_root,
                label="render_request",
            )
        )

    lifecycle_events = [
        dict(event)
        for event in (polish_lifecycle or {}).get("events", [])
        if isinstance(event, Mapping) and str(event.get("figure_id") or "") == figure_id
    ]
    workflow_figures = [
        dict(item)
        for item in (workflow_packet or {}).get("figures", [])
        if isinstance(item, Mapping) and str(item.get("figure_id") or "") == figure_id
    ]
    visual_artifacts = [
        dict(item)
        for item in (visual_audit_receipt or {}).get("inspected_artifacts", [])
        if isinstance(item, Mapping) and str(item.get("figure_id") or "") == figure_id
    ]

    created_at = _utc_now()
    metadata = {
        "schema_version": 1,
        "surface_kind": "display_pack_figure_provenance_bundle",
        "figure_id": figure_id,
        "created_at": created_at,
        "repo_root": str(repo_root),
        "paper_root": str(paper_root),
        "source_surfaces": {
            "refs": source_surface_refs,
        },
        "code": {
            "template_id": template_id,
            "renderer_family": str(figure.get("renderer_family") or render_figure.get("selected_backend") or ""),
            "execution_mode": str(figure.get("execution_mode") or render_figure.get("execution_mode") or ""),
            "entrypoint": str(render_result.get("entrypoint") or template_entry.get("entrypoint") or ""),
            "refs": code_refs,
        },
        "input": {
            "claim_ref": str(figure.get("claim_ref") or ""),
            "data_refs": data_refs,
            "source_data_digests": dict(render_figure.get("source_data_digests") or {}),
            "statistics_refs": list(render_figure.get("statistics_refs") or figure.get("statistical_value_refs") or []),
            "publication_style_profile": style_profile,
            "refs": input_refs,
        },
        "output": {
            "rendered_artifacts": rendered,
            "deterministic_qc": dict(figure.get("deterministic_qc") or {}),
            "refs": output_refs,
        },
        "environment": {
            "dependency_environment": dependency_environment,
            "render_result": render_result,
            "refs": environment_refs,
        },
        "agent_trace": {
            "summary": "refs_only_agent_trace; full Codex transcript is not captured by Display Pack outputs",
            "workflow_status": str((workflow_packet or {}).get("workflow_status") or ""),
            "workflow_figure": workflow_figures[0] if workflow_figures else {},
            "polish_lifecycle_events": lifecycle_events,
            "codex_transcript": {
                "status": "restricted",
                "reason": "not_part_of_display_pack_receipts",
                "locator": "external_agent_session_history",
            },
        },
        "reviews": {
            "visual_audit_final_status": str((visual_audit_receipt or {}).get("final_status") or ""),
            "visual_audit_artifacts": visual_artifacts,
            "finding_count": len((visual_audit_receipt or {}).get("findings") or []),
            "refs": review_refs,
        },
        "replay": {
            "mode": "refs_only_no_rerun",
            "entrypoint": str(render_result.get("entrypoint") or template_entry.get("entrypoint") or ""),
            "argv": list(render_result.get("argv") or []),
            "cwd": str(render_result.get("cwd") or ""),
            "request_ref": str(render_result.get("request_ref") or ""),
            "expected_output_refs": [
                ref
                for ref in (
                    rendered.get("png_ref"),
                    rendered.get("pdf_ref"),
                    rendered.get("layout_sidecar_ref"),
                )
                if ref
            ],
            "refs": replay_refs,
        },
        "authority_boundary": {
            "bundle_is_projection_from_existing_display_pack_outputs": True,
            "can_authorize_publication_readiness": False,
            "can_authorize_quality_verdict": False,
            "can_mutate_data_or_statistics": False,
            "can_replace_visual_audit": False,
            "can_replace_owner_receipt": False,
            "does_not_rerun_or_rewrite_figures": True,
        },
    }
    missing_refs = _bundle_missing_refs(metadata)
    restricted_refs = _bundle_restricted_refs(metadata)
    hashes = _hashes_from_refs(
        source_surface_refs,
        code_refs,
        input_refs,
        output_refs,
        environment_refs,
        review_refs,
        replay_refs,
    )
    if not hashes:
        hashes["bundle_metadata"] = {"algorithm": "sha256", "value": _sha256_text(json.dumps(metadata, sort_keys=True))}
    bundle = {
        "schema_version": "artifact-provenance-bundle.v1",
        "bundle_id": f"medautoscience:display-pack-figure:{figure_id}",
        "artifact_ref": str(rendered.get("png_ref") or rendered.get("pdf_ref") or f"medautoscience:figure:{figure_id}"),
        "domain_id": "medautoscience",
        "artifact_type": "display_pack_figure",
        "created_at": created_at,
        "refs": {
            "code": _ref_values(code_refs),
            "inputs": _ref_values(source_surface_refs + input_refs),
            "outputs": _ref_values(output_refs),
            "environment": _ref_values(environment_refs),
            "agent_trace": [FIGURE_WORKFLOW_PACKET_REF, FIGURE_POLISH_LIFECYCLE_REF],
            "reviews": _ref_values(review_refs),
            "replay": _ref_values(replay_refs),
        },
        "hashes": hashes,
        "authority_boundary": {
            "ledger_refs_only": True,
            "forbidden_claims": [
                "publication_readiness",
                "quality_verdict",
                "artifact_authority",
                "owner_receipt",
                "domain_ready",
                "production_ready",
            ],
            "can_read_artifact_body": False,
            "can_store_artifact_body": False,
            "can_mutate_artifact_body": False,
            "can_write_domain_truth": False,
            "can_create_owner_receipt": False,
            "can_authorize_quality_verdict": False,
            "can_claim_domain_ready": False,
            "can_claim_artifact_ready": False,
            "can_claim_production_ready": False,
        },
        "metadata": metadata,
        "missing_refs": missing_refs,
        "restricted_refs": restricted_refs,
    }
    return bundle


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
        )
        bundle_ref = f"{PROVENANCE_BUNDLE_REF_PREFIX}/{_safe_figure_dir(figure_id)}/bundle.json"
        bundle_path = _resolve_ref_path(bundle_ref, paper_root=normalized_paper_root)
        _write_json(bundle_path, bundle)
        bundles.append(
            {
                "figure_id": figure_id,
                "provenance_bundle_ref": bundle_ref,
                "provenance_bundle_hash": _sha256_file(bundle_path),
                "missing_ref_count": len(bundle["missing_refs"]),
                "restricted_ref_count": len(bundle["restricted_refs"]),
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
