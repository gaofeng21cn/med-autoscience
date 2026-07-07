from __future__ import annotations

from collections.abc import Mapping
import json
from pathlib import Path
from typing import Any

from .refs import (
    AGENT_TRACE_REFS_REF,
    FIGURE_POLISH_LIFECYCLE_REF,
    FIGURE_VISUAL_AUDIT_RECEIPT_REF,
    FIGURE_WORKFLOW_PACKET_REF,
    _agent_trace_ref_specs,
    _bundle_missing_refs,
    _bundle_restricted_refs,
    _bundle_typed_issues,
    _expected_output_entries,
    _file_ref,
    _figures_by_id,
    _global_surface_refs,
    _hashes_from_refs,
    _list_file_refs,
    _ref_from_path,
    _ref_values,
    _renderer_code_ref,
    _replay_status,
    _sha256_text,
    _template_lock_entry,
    _utc_now,
)


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
    agent_trace_refs: Mapping[str, Any] | None,
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
        _file_ref(
            ref,
            paper_root=paper_root,
            repo_root=repo_root,
            label=label,
            required=True,
            include_sha256=include_sha256,
            sha256_omitted_reason="omitted_to_avoid_reverse_provenance_hash_cycle",
        )
        for label, ref, include_sha256 in _global_surface_refs()
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

    agent_trace_external_refs = [
        _file_ref(
            str(item["ref"]),
            paper_root=paper_root,
            repo_root=repo_root,
            label=str(item["label"]),
            required=bool(item["required"]),
        )
        for item in _agent_trace_ref_specs(agent_trace_refs)
    ]
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
    expected_outputs = _expected_output_entries(
        rendered,
        paper_root=paper_root,
        repo_root=repo_root,
    )
    replay_status = _replay_status(
        render_result=render_result,
        replay_refs=replay_refs,
        expected_outputs=expected_outputs,
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
            "summary": "refs_only_agent_trace; attach full transcript or message-history files through agent_trace_refs when available",
            "workflow_status": str((workflow_packet or {}).get("workflow_status") or ""),
            "workflow_figure": workflow_figures[0] if workflow_figures else {},
            "polish_lifecycle_events": lifecycle_events,
            "agent_trace_refs_ref": AGENT_TRACE_REFS_REF if agent_trace_refs is not None else "",
            "external_trace_refs": agent_trace_external_refs,
            "codex_transcript": {
                "status": "ref_available" if agent_trace_external_refs else "restricted",
                "reason": "external_agent_session_history_ref" if agent_trace_external_refs else "not_part_of_display_pack_receipts",
                "locator": "agent_trace_refs" if agent_trace_external_refs else "external_agent_session_history",
            },
            "refs": agent_trace_external_refs,
        },
        "reviews": {
            "visual_audit_final_status": str((visual_audit_receipt or {}).get("final_status") or ""),
            "visual_audit_artifacts": visual_artifacts,
            "finding_count": len((visual_audit_receipt or {}).get("findings") or []),
            "refs": review_refs,
        },
        "replay": {
            "mode": "refs_only_no_rerun",
            "status": replay_status["status"],
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
            "expected_outputs": expected_outputs,
            "dry_run_readback": replay_status,
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
    typed_issues = _bundle_typed_issues(
        metadata=metadata,
        missing_refs=missing_refs,
        restricted_refs=restricted_refs,
        replay_status=replay_status,
    )
    metadata["typed_issues"] = typed_issues
    hashes = _hashes_from_refs(
        source_surface_refs,
        code_refs,
        input_refs,
        output_refs,
        environment_refs,
        agent_trace_external_refs,
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
            "agent_trace": [FIGURE_WORKFLOW_PACKET_REF, FIGURE_POLISH_LIFECYCLE_REF, *_ref_values(agent_trace_external_refs)],
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
        "typed_issues": typed_issues,
    }
    return bundle
