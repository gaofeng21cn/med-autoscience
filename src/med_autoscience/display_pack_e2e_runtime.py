from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import time
from typing import Any

from med_autoscience import display_layout_qc
from med_autoscience.display_pack_lock import write_display_pack_lock
from med_autoscience.display_pack_runtime import (
    load_python_plugin_callable,
    resolve_display_template_runtime,
)
from med_autoscience.figure_polish_lifecycle_contract import load_figure_polish_lifecycle
from med_autoscience.medical_figure_spec_contract import (
    MEDICAL_FIGURE_SPEC_BASENAME,
    MEDICAL_FIGURE_SPECS_BASENAME,
    load_medical_figure_spec,
    load_medical_figure_specs,
)
from med_autoscience.publication_display_contract import (
    load_display_overrides,
    load_publication_style_profile,
    resolve_style_roles,
)
from med_autoscience.publication_figure_quality_contract import (
    collect_publication_figure_quality_refs,
    load_figure_intent,
    load_figure_style_reference_bundle,
    load_figure_visual_audit_receipt,
)
from med_autoscience.runtime_protocol.display_artifact_manifest import build_display_artifact_manifest


PUBLICATION_MANIFEST_BASENAME = "display_pack_publication_manifest.json"
DISPLAY_PACK_LOCK_REF = "paper/build/display_pack_lock.json"
FIGURE_VISUAL_AUDIT_RECEIPT_REF = "paper/figure_visual_audit_receipt.json"
FIGURE_POLISH_LIFECYCLE_REF = "paper/figure_polish_lifecycle.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _read_json_object(path: Path) -> dict[str, Any]:
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


def _json_compatible(value: object, *, field_name: str) -> object:
    try:
        json.dumps(value, ensure_ascii=False)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be JSON-serializable") from exc
    return value


def _workspace_ref(path: Path, *, paper_root: Path) -> str:
    return path.resolve().relative_to(paper_root.resolve().parent).as_posix()


def _resolve_workspace_ref(ref: str, *, paper_root: Path) -> Path:
    normalized = str(ref or "").strip()
    if not normalized:
        raise ValueError("workspace ref must be non-empty")
    path = Path(normalized).expanduser()
    if path.is_absolute():
        return path.resolve()
    if path.parts and path.parts[0] == paper_root.name:
        return (paper_root.parent / path).resolve()
    return (paper_root / path).resolve()


def _safe_artifact_stem(figure_id: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", figure_id.strip())
    if not normalized:
        raise ValueError("figure_id must produce a non-empty artifact stem")
    return normalized


def _intent_figure(intent_payload: Mapping[str, Any], *, figure_id: str) -> dict[str, Any]:
    figures = intent_payload.get("figures")
    if not isinstance(figures, list):
        raise ValueError("figure_intent.figures must be a list")
    matches = [item for item in figures if isinstance(item, dict) and item.get("figure_id") == figure_id]
    if len(matches) != 1:
        raise ValueError(f"figure_intent must contain exactly one figure for `{figure_id}`")
    return dict(matches[0])


def _load_required_quality_inputs(paper_root: Path) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    intent = load_figure_intent(paper_root / "figure_intent.json")
    batch_spec_path = paper_root / MEDICAL_FIGURE_SPECS_BASENAME
    if batch_spec_path.exists():
        figure_specs = list(load_medical_figure_specs(batch_spec_path)["figures"])
    else:
        figure_specs = [load_medical_figure_spec(paper_root / MEDICAL_FIGURE_SPEC_BASENAME)]
    style_reference_bundle = load_figure_style_reference_bundle(paper_root / "figure_style_reference_bundle.json")
    return intent, figure_specs, style_reference_bundle


def _validate_intent_spec_binding(*, intent_figure: Mapping[str, Any], figure_spec: Mapping[str, Any]) -> None:
    for field_name in ("figure_id", "template_id", "figure_kind"):
        if intent_figure.get(field_name) != figure_spec.get(field_name):
            raise ValueError(
                f"figure_intent.{field_name} and medical_figure_spec.{field_name} must match "
                f"for `{figure_spec.get('figure_id')}`"
            )


def _style_render_context(
    *,
    paper_root: Path,
    figure_id: str,
    full_template_id: str,
    short_template_id: str,
) -> dict[str, Any]:
    style_profile = load_publication_style_profile(paper_root / "publication_style_profile.json")
    overrides = load_display_overrides(paper_root / "display_overrides.json")
    override = (
        overrides.get((figure_id, full_template_id))
        or overrides.get((figure_id, short_template_id))
    )
    return {
        "style_profile_id": style_profile.style_profile_id,
        "style_roles": resolve_style_roles(
            style_profile=style_profile,
            template_id=short_template_id,
        ),
        "layout_override": dict(override.layout_override) if override is not None else {},
        "readability_override": dict(override.readability_override) if override is not None else {},
    }


def _data_payload_and_digest(*, paper_root: Path, data_ref: str) -> tuple[dict[str, Any], str]:
    data_path = _resolve_workspace_ref(data_ref, paper_root=paper_root)
    data_payload = _read_json_object(data_path)
    digest = str(data_payload.get("source_data_digest") or "").strip()
    if not digest:
        digest = _sha256_file(data_path)
    return data_payload, digest


def _subprocess_placeholders(
    *,
    request_path: Path,
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
    figure_id: str,
    paper_root: Path,
    template_root: Path,
    pack_root: Path,
) -> dict[str, str]:
    return {
        "request_json": str(request_path),
        "input_json": str(request_path),
        "output_png": str(output_png_path),
        "output_pdf": str(output_pdf_path),
        "layout_sidecar": str(layout_sidecar_path),
        "figure_id": figure_id,
        "paper_root": str(paper_root),
        "template_root": str(template_root),
        "pack_root": str(pack_root),
    }


def _expand_subprocess_entrypoint(entrypoint: str, *, placeholders: Mapping[str, str]) -> list[str]:
    raw_argv = shlex.split(entrypoint)
    if not raw_argv:
        raise ValueError("subprocess display template entrypoint must not be empty")
    expanded: list[str] = []
    for token in raw_argv:
        expanded_token = token
        for placeholder, value in placeholders.items():
            expanded_token = expanded_token.replace("{" + placeholder + "}", value)
        if "{" in expanded_token or "}" in expanded_token:
            raise ValueError(f"unsupported subprocess renderer placeholder in `{entrypoint}`")
        expanded.append(expanded_token)
    return expanded


def _run_subprocess_renderer(
    *,
    runtime_template_root: Path,
    pack_root: Path,
    template_manifest: Any,
    paper_root: Path,
    figure_id: str,
    full_template_id: str,
    display_payload: Mapping[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> dict[str, Any]:
    request_dir = paper_root / "build" / "display_pack_render_requests"
    log_dir = paper_root / "build" / "display_pack_renderer_logs"
    request_path = request_dir / f"{_safe_artifact_stem(figure_id)}.render_request.json"
    stdout_path = log_dir / f"{_safe_artifact_stem(figure_id)}.stdout.txt"
    stderr_path = log_dir / f"{_safe_artifact_stem(figure_id)}.stderr.txt"
    render_request = {
        "schema_version": 1,
        "execution_mode": "subprocess",
        "renderer_family": template_manifest.renderer_family,
        "figure_id": figure_id,
        "template_id": full_template_id,
        "short_template_id": template_manifest.template_id,
        "display_payload": dict(display_payload),
        "output_png_path": str(output_png_path),
        "output_pdf_path": str(output_pdf_path),
        "layout_sidecar_path": str(layout_sidecar_path),
    }
    _write_json(request_path, render_request)
    placeholders = _subprocess_placeholders(
        request_path=request_path,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
        figure_id=figure_id,
        paper_root=paper_root,
        template_root=runtime_template_root,
        pack_root=pack_root,
    )
    argv = _expand_subprocess_entrypoint(template_manifest.entrypoint, placeholders=placeholders)
    env = {
        **os.environ,
        "MAS_DISPLAY_RENDER_REQUEST": str(request_path),
        "MAS_DISPLAY_OUTPUT_PNG": str(output_png_path),
        "MAS_DISPLAY_OUTPUT_PDF": str(output_pdf_path),
        "MAS_DISPLAY_LAYOUT_SIDECAR": str(layout_sidecar_path),
        "MAS_DISPLAY_FIGURE_ID": figure_id,
        "MAS_DISPLAY_TEMPLATE_ID": full_template_id,
    }
    started_at = time.monotonic()
    completed = subprocess.run(
        argv,
        cwd=runtime_template_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
        env=env,
    )
    duration_seconds = round(time.monotonic() - started_at, 3)
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    result = {
        "status": "rendered" if completed.returncode == 0 else "failed",
        "execution_mode": "subprocess",
        "renderer_family": template_manifest.renderer_family,
        "entrypoint": template_manifest.entrypoint,
        "argv": argv,
        "cwd": str(runtime_template_root),
        "returncode": completed.returncode,
        "duration_seconds": duration_seconds,
        "request_path": str(request_path),
        "request_ref": _workspace_ref(request_path, paper_root=paper_root),
        "stdout_path": str(stdout_path),
        "stdout_ref": _workspace_ref(stdout_path, paper_root=paper_root),
        "stderr_path": str(stderr_path),
        "stderr_ref": _workspace_ref(stderr_path, paper_root=paper_root),
    }
    if completed.returncode != 0:
        raise ValueError(
            f"subprocess display renderer failed for `{figure_id}` with return code "
            f"{completed.returncode}; stderr ref: {result['stderr_ref']}"
        )
    return result


def _run_candidate_subprocess_renderer(
    *,
    runtime_template_root: Path,
    pack_root: Path,
    paper_root: Path,
    figure_id: str,
    full_template_id: str,
    short_template_id: str,
    display_payload: Mapping[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> dict[str, Any]:
    request_dir = paper_root / "requests"
    log_dir = paper_root / "logs"
    request_path = request_dir / f"{_safe_artifact_stem(figure_id)}.render_candidate_request.json"
    stdout_path = log_dir / f"{_safe_artifact_stem(figure_id)}.stdout.txt"
    stderr_path = log_dir / f"{_safe_artifact_stem(figure_id)}.stderr.txt"
    render_request = {
        "schema_version": 1,
        "execution_mode": "subprocess",
        "renderer_family": "r_ggplot2",
        "candidate_only": True,
        "comparison_only": True,
        "figure_id": figure_id,
        "template_id": full_template_id,
        "short_template_id": short_template_id,
        "display_payload": dict(display_payload),
        "output_png_path": str(output_png_path),
        "output_pdf_path": str(output_pdf_path),
        "layout_sidecar_path": str(layout_sidecar_path),
    }
    _write_json(request_path, render_request)
    entrypoint = "Rscript render_candidate.R --request {request_json}"
    placeholders = _subprocess_placeholders(
        request_path=request_path,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
        figure_id=figure_id,
        paper_root=paper_root,
        template_root=runtime_template_root,
        pack_root=pack_root,
    )
    argv = _expand_subprocess_entrypoint(entrypoint, placeholders=placeholders)
    env = {
        **os.environ,
        "MAS_DISPLAY_RENDER_REQUEST": str(request_path),
        "MAS_DISPLAY_OUTPUT_PNG": str(output_png_path),
        "MAS_DISPLAY_OUTPUT_PDF": str(output_pdf_path),
        "MAS_DISPLAY_LAYOUT_SIDECAR": str(layout_sidecar_path),
        "MAS_DISPLAY_FIGURE_ID": figure_id,
        "MAS_DISPLAY_TEMPLATE_ID": full_template_id,
        "MAS_DISPLAY_RENDERER_CANDIDATE_ONLY": "1",
    }
    started_at = time.monotonic()
    completed = subprocess.run(
        argv,
        cwd=runtime_template_root,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
        env=env,
    )
    duration_seconds = round(time.monotonic() - started_at, 3)
    stdout_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.parent.mkdir(parents=True, exist_ok=True)
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    result = {
        "status": "rendered" if completed.returncode == 0 else "failed",
        "execution_mode": "subprocess",
        "renderer_family": "r_ggplot2",
        "candidate_entrypoint": entrypoint,
        "argv": argv,
        "cwd": str(runtime_template_root),
        "returncode": completed.returncode,
        "duration_seconds": duration_seconds,
        "request_path": str(request_path),
        "request_ref": _workspace_ref(request_path, paper_root=paper_root),
        "stdout_path": str(stdout_path),
        "stdout_ref": _workspace_ref(stdout_path, paper_root=paper_root),
        "stderr_path": str(stderr_path),
        "stderr_ref": _workspace_ref(stderr_path, paper_root=paper_root),
    }
    if completed.returncode != 0:
        raise ValueError(
            f"candidate display renderer failed for `{figure_id}` with return code "
            f"{completed.returncode}; stderr ref: {result['stderr_ref']}"
        )
    return result


def _run_python_plugin_renderer(
    *,
    repo_root: Path,
    paper_root: Path,
    template_manifest: Any,
    full_template_id: str,
    display_payload: Mapping[str, Any],
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
) -> dict[str, Any]:
    renderer = load_python_plugin_callable(
        repo_root=repo_root,
        paper_root=paper_root,
        template_id=full_template_id,
    )
    plugin_result = renderer(
        template_id=full_template_id,
        display_payload=display_payload,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )
    if isinstance(plugin_result, Mapping):
        return {
            "execution_mode": "python_plugin",
            "renderer_family": template_manifest.renderer_family,
            **dict(plugin_result),
        }
    return {
        "status": "rendered",
        "execution_mode": "python_plugin",
        "renderer_family": template_manifest.renderer_family,
        "plugin_result": plugin_result,
    }


def _render_figure(
    *,
    repo_root: Path,
    paper_root: Path,
    figure_spec: Mapping[str, Any],
    intent_figure: Mapping[str, Any],
) -> dict[str, Any]:
    figure_id = str(figure_spec["figure_id"])
    full_template_id = str(figure_spec["template_id"])
    runtime = resolve_display_template_runtime(
        repo_root=repo_root,
        paper_root=paper_root,
        template_id=full_template_id,
    )
    template_manifest = runtime.template_manifest
    data_payload, data_digest = _data_payload_and_digest(
        paper_root=paper_root,
        data_ref=str(intent_figure["data_ref"]),
    )
    stem = _safe_artifact_stem(figure_id)
    output_dir = paper_root / "figures" / "generated"
    output_png_path = output_dir / f"{stem}.png"
    output_pdf_path = output_dir / f"{stem}.pdf"
    layout_sidecar_path = output_dir / f"{stem}.layout.json"
    render_context = _style_render_context(
        paper_root=paper_root,
        figure_id=figure_id,
        full_template_id=full_template_id,
        short_template_id=template_manifest.template_id,
    )
    display_payload = {
        "figure_id": figure_id,
        "template_id": full_template_id,
        "figure_kind": figure_spec["figure_kind"],
        "medical_semantics": dict(figure_spec["medical_semantics"]),
        "panels": list(figure_spec.get("panels") or []),
        "claim_ref": intent_figure["claim_ref"],
        "data_ref": intent_figure["data_ref"],
        "data_payload": data_payload,
        "render_context": render_context,
    }
    if template_manifest.execution_mode == "python_plugin":
        render_result = _run_python_plugin_renderer(
            repo_root=repo_root,
            paper_root=paper_root,
            template_manifest=template_manifest,
            full_template_id=full_template_id,
            display_payload=display_payload,
            output_png_path=output_png_path,
            output_pdf_path=output_pdf_path,
            layout_sidecar_path=layout_sidecar_path,
        )
    elif template_manifest.execution_mode == "subprocess":
        render_result = _run_subprocess_renderer(
            runtime_template_root=runtime.template_path.parent,
            pack_root=runtime.pack_root,
            template_manifest=template_manifest,
            paper_root=paper_root,
            figure_id=figure_id,
            full_template_id=full_template_id,
            display_payload=display_payload,
            output_png_path=output_png_path,
            output_pdf_path=output_pdf_path,
            layout_sidecar_path=layout_sidecar_path,
        )
    else:
        raise ValueError(f"unsupported display template execution mode `{template_manifest.execution_mode}`")
    for path in (output_png_path, output_pdf_path, layout_sidecar_path):
        if not path.exists():
            raise FileNotFoundError(f"display pack renderer did not write required artifact: {path}")
    layout_sidecar = _read_json_object(layout_sidecar_path)
    qc_result = display_layout_qc.run_display_layout_qc(
        qc_profile=template_manifest.qc_profile_ref,
        layout_sidecar=layout_sidecar,
    )
    qc_path = paper_root / "qc" / f"{stem}.layout_qc.json"
    _write_json(qc_path, qc_result)
    if qc_result.get("status") != "pass":
        raise ValueError(f"deterministic QC failed for `{figure_id}`: {qc_result.get('failure_reason')}")
    return {
        "figure_id": figure_id,
        "template_id": full_template_id,
        "short_template_id": template_manifest.template_id,
        "figure_kind": figure_spec["figure_kind"],
        "renderer_family": template_manifest.renderer_family,
        "execution_mode": template_manifest.execution_mode,
        "claim_ref": intent_figure["claim_ref"],
        "data_ref": intent_figure["data_ref"],
        "data_digest": data_digest,
        "statistical_value_refs": list(intent_figure.get("statistical_value_refs") or []),
        "qc_profile": template_manifest.qc_profile_ref,
        "render_result": _json_compatible(render_result, field_name="display_pack_renderer.render_result"),
        "rendered_artifacts": {
            "png_path": str(output_png_path),
            "pdf_path": str(output_pdf_path),
            "layout_sidecar_path": str(layout_sidecar_path),
            "png_ref": _workspace_ref(output_png_path, paper_root=paper_root),
            "pdf_ref": _workspace_ref(output_pdf_path, paper_root=paper_root),
            "layout_sidecar_ref": _workspace_ref(layout_sidecar_path, paper_root=paper_root),
            "png_sha256": _sha256_file(output_png_path),
            "pdf_sha256": _sha256_file(output_pdf_path),
            "layout_sidecar_sha256": _sha256_file(layout_sidecar_path),
        },
        "deterministic_qc": {
            **qc_result,
            "path": str(qc_path),
            "ref": _workspace_ref(qc_path, paper_root=paper_root),
            "sha256": _sha256_file(qc_path),
        },
    }


def _visual_audit_receipt_payload(
    *,
    figure_entries: list[dict[str, Any]],
    visual_audit_review: Mapping[str, Any],
) -> dict[str, Any]:
    audit_mode = str(visual_audit_review.get("audit_mode") or "").strip() or "human_visual_review"
    final_status = str(visual_audit_review.get("final_status") or "").strip() or "clear"
    reviewer = visual_audit_review.get("reviewer")
    if not isinstance(reviewer, Mapping):
        review_label = json.dumps(visual_audit_review, ensure_ascii=False, sort_keys=True)
        reviewer = {
            "provider": "mas-local-reviewer",
            "model": "structured-visual-review",
            "prompt_hash": _sha256_text(review_label),
        }
    findings = visual_audit_review.get("findings")
    if findings is None:
        findings = []
    if not isinstance(findings, list):
        raise ValueError("visual_audit_review.findings must be a list when provided")
    return {
        "schema_version": 1,
        "receipt_id": f"display-pack-visual-audit-{_utc_now()}",
        "audit_mode": audit_mode,
        "inspected_artifacts": [
            {
                "figure_id": entry["figure_id"],
                "artifact_path": entry["rendered_artifacts"]["png_ref"],
                "artifact_sha256": entry["rendered_artifacts"]["png_sha256"],
            }
            for entry in figure_entries
        ],
        "findings": findings,
        "reviewer": dict(reviewer),
        "final_status": final_status,
    }


def _write_visual_audit_receipt(
    *,
    paper_root: Path,
    figure_entries: list[dict[str, Any]],
    visual_audit_review: Mapping[str, Any],
) -> dict[str, Any]:
    receipt_path = paper_root / "figure_visual_audit_receipt.json"
    payload = _visual_audit_receipt_payload(
        figure_entries=figure_entries,
        visual_audit_review=visual_audit_review,
    )
    _write_json(receipt_path, payload)
    return load_figure_visual_audit_receipt(receipt_path)


def _write_figure_polish_lifecycle(
    *,
    paper_root: Path,
    figure_entries: list[dict[str, Any]],
    audit_receipt: Mapping[str, Any],
) -> dict[str, Any]:
    if audit_receipt.get("final_status") != "clear":
        raise ValueError("publication manifest requires clear visual audit status")
    audit_actor = str(audit_receipt.get("audit_mode") or "").strip() or "human_visual_review"
    events: list[dict[str, Any]] = []
    for entry in figure_entries:
        figure_id = str(entry["figure_id"])
        artifact_ref = str(entry["rendered_artifacts"]["png_ref"])
        qc_ref = str(entry["deterministic_qc"]["ref"])
        events.extend(
            [
                {
                    "state": "draft_rendered",
                    "figure_id": figure_id,
                    "artifact_ref": artifact_ref,
                    "actor": "display_pack_builder",
                    "evidence_ref": DISPLAY_PACK_LOCK_REF,
                    "mutates_data": False,
                    "carries_publication_verdict": False,
                },
                {
                    "state": "deterministic_qc_clear",
                    "figure_id": figure_id,
                    "artifact_ref": artifact_ref,
                    "actor": "deterministic_qc",
                    "evidence_ref": qc_ref,
                    "mutates_data": False,
                    "carries_publication_verdict": False,
                },
                {
                    "state": "visual_audit_findings",
                    "figure_id": figure_id,
                    "artifact_ref": artifact_ref,
                    "actor": audit_actor,
                    "evidence_ref": FIGURE_VISUAL_AUDIT_RECEIPT_REF,
                    "reviewer_ref": "paper/figure_visual_audit_receipt.json#/reviewer",
                    "mutates_data": False,
                    "carries_publication_verdict": False,
                },
                {
                    "state": "revised",
                    "figure_id": figure_id,
                    "artifact_ref": artifact_ref,
                    "actor": "display_pack_builder",
                    "evidence_ref": qc_ref,
                    "mutates_data": False,
                    "carries_publication_verdict": False,
                },
                {
                    "state": "audit_clear",
                    "figure_id": figure_id,
                    "artifact_ref": artifact_ref,
                    "actor": audit_actor,
                    "evidence_ref": FIGURE_VISUAL_AUDIT_RECEIPT_REF,
                    "reviewer_ref": "paper/figure_visual_audit_receipt.json#/reviewer",
                    "mutates_data": False,
                    "carries_publication_verdict": False,
                },
                {
                    "state": "publication_manifested",
                    "figure_id": figure_id,
                    "artifact_ref": artifact_ref,
                    "actor": "display_pack_builder",
                    "evidence_ref": "paper/build/display_pack_publication_manifest.json",
                    "mutates_data": False,
                    "carries_publication_verdict": False,
                },
            ]
        )
    lifecycle_payload = {
        "schema_version": 1,
        "lifecycle_id": "display-pack-polish",
        "relationship_refs": {
            "figure_visual_audit_receipt": FIGURE_VISUAL_AUDIT_RECEIPT_REF,
            "display_pack_lock_publication_figure_quality_refs": (
                f"{DISPLAY_PACK_LOCK_REF}#/publication_figure_quality_refs"
            ),
        },
        "events": events,
    }
    lifecycle_path = paper_root / "figure_polish_lifecycle.json"
    _write_json(lifecycle_path, lifecycle_payload)
    return load_figure_polish_lifecycle(lifecycle_path)


def _write_display_artifact_manifest(
    *,
    paper_root: Path,
    figure_entry: Mapping[str, Any],
) -> dict[str, Any]:
    statistical_value_refs = list(figure_entry.get("statistical_value_refs") or [])
    if not statistical_value_refs:
        statistical_value_refs = [f"{figure_entry['data_ref']}#/source_data_digest"]
    manifest = build_display_artifact_manifest(
        artifact_id=str(figure_entry["figure_id"]),
        artifact_kind=str(figure_entry["figure_kind"]),
        source_data_refs=[str(figure_entry["data_ref"])],
        source_data_digests={str(figure_entry["data_ref"]): str(figure_entry["data_digest"])},
        claim_refs=[str(figure_entry["claim_ref"])],
        statistical_value_refs=statistical_value_refs,
        rendered_artifact_ref=str(figure_entry["rendered_artifacts"]["png_ref"]),
        rendered_artifact_digest=str(figure_entry["rendered_artifacts"]["png_sha256"]),
        placement={"placement": "single_column", "paper_role": "main_text"},
        scalable=True,
        protected=True,
        visual_qa_receipt_refs=[FIGURE_VISUAL_AUDIT_RECEIPT_REF],
        currentness={
            "status": "current",
            "checked_at": _utc_now(),
            "display_pack_lock_ref": DISPLAY_PACK_LOCK_REF,
        },
    )
    output_path = paper_root / "build" / f"display_artifact_manifest.{figure_entry['figure_id']}.json"
    _write_json(output_path, manifest)
    return {
        "path": str(output_path),
        "ref": _workspace_ref(output_path, paper_root=paper_root),
        "sha256": _sha256_file(output_path),
        "payload": manifest,
    }


def materialize_display_pack_publication_manifest(
    *,
    repo_root: Path,
    paper_root: Path,
    visual_audit_review: Mapping[str, Any],
    figure_ids: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    normalized_repo_root = Path(repo_root).expanduser().resolve()
    normalized_paper_root = Path(paper_root).expanduser().resolve()
    intent, loaded_figure_specs, _style_reference_bundle = _load_required_quality_inputs(normalized_paper_root)
    requested_figure_ids = [str(item).strip() for item in (figure_ids or []) if str(item).strip()]
    if requested_figure_ids:
        specs_by_id = {str(item["figure_id"]): item for item in loaded_figure_specs}
        missing = [figure_id for figure_id in requested_figure_ids if figure_id not in specs_by_id]
        if missing:
            raise ValueError(f"requested figure_id not found in medical figure specs: {missing[0]}")
        figure_specs = [specs_by_id[figure_id] for figure_id in requested_figure_ids]
    else:
        figure_specs = loaded_figure_specs

    figure_entries = []
    for figure_spec in figure_specs:
        figure_id = str(figure_spec["figure_id"])
        intent_figure = _intent_figure(intent, figure_id=figure_id)
        _validate_intent_spec_binding(intent_figure=intent_figure, figure_spec=figure_spec)
        figure_entries.append(
            _render_figure(
                repo_root=normalized_repo_root,
                paper_root=normalized_paper_root,
                figure_spec=figure_spec,
                intent_figure=intent_figure,
            )
        )
    audit_receipt = _write_visual_audit_receipt(
        paper_root=normalized_paper_root,
        figure_entries=figure_entries,
        visual_audit_review=visual_audit_review,
    )
    lifecycle = _write_figure_polish_lifecycle(
        paper_root=normalized_paper_root,
        figure_entries=figure_entries,
        audit_receipt=audit_receipt,
    )
    artifact_manifest_refs = [
        _write_display_artifact_manifest(
            paper_root=normalized_paper_root,
            figure_entry=entry,
        )
        for entry in figure_entries
    ]
    lock_path = write_display_pack_lock(
        paper_root=normalized_paper_root,
        repo_root=normalized_repo_root,
    )
    quality_refs = collect_publication_figure_quality_refs(paper_root=normalized_paper_root)
    manifest_path = normalized_paper_root / "build" / PUBLICATION_MANIFEST_BASENAME
    manifest = {
        "schema_version": 1,
        "status": "publication_manifested",
        "manifest_path": str(manifest_path),
        "created_at": _utc_now(),
        "repo_root": str(normalized_repo_root),
        "paper_root": str(normalized_paper_root),
        "display_pack_lock_path": str(lock_path),
        "display_pack_lock_ref": _workspace_ref(lock_path, paper_root=normalized_paper_root),
        "display_pack_lock_sha256": _sha256_file(lock_path),
        "publication_readiness_verdict": False,
        "authority_boundary": {
            "mas_display_artifact_authority": True,
            "mas_publication_quality_authority": True,
            "opl_pack_os_lifecycle_owner": True,
            "display_pack_lock_can_authorize_publication_readiness": False,
            "ai_visual_audit_can_mutate_data_or_statistics": False,
        },
        "publication_figure_quality_refs": quality_refs,
        "figure_polish_lifecycle": {
            "path": str(normalized_paper_root / "figure_polish_lifecycle.json"),
            "ref": FIGURE_POLISH_LIFECYCLE_REF,
            "states": [event["state"] for event in lifecycle["events"]],
        },
        "visual_audit": {
            "path": str(normalized_paper_root / "figure_visual_audit_receipt.json"),
            "ref": FIGURE_VISUAL_AUDIT_RECEIPT_REF,
            "final_status": audit_receipt["final_status"],
            "finding_count": len(audit_receipt["findings"]),
        },
        "display_artifact_manifests": [
            {key: value for key, value in item.items() if key != "payload"}
            for item in artifact_manifest_refs
        ],
        "figures": figure_entries,
    }
    _write_json(manifest_path, manifest)
    return manifest


def render_display_pack_candidate_asset(
    *,
    repo_root: Path,
    template_id: str,
    display_payload_file: Path,
    output_dir: Path,
) -> dict[str, Any]:
    normalized_repo_root = Path(repo_root).expanduser().resolve()
    normalized_output_dir = Path(output_dir).expanduser().resolve()
    payload_path = Path(display_payload_file).expanduser().resolve()
    display_payload = _read_json_object(payload_path)
    runtime = resolve_display_template_runtime(
        repo_root=normalized_repo_root,
        paper_root=None,
        template_id=template_id,
    )
    template_manifest = runtime.template_manifest
    candidate_script_path = runtime.template_path.parent / "render_candidate.R"
    if not candidate_script_path.is_file():
        raise ValueError(
            f"display template `{template_id}` does not provide render_candidate.R"
        )
    figure_id = f"candidate-{template_manifest.template_id}"
    stem = _safe_artifact_stem(template_manifest.template_id)
    output_png_path = normalized_output_dir / f"{stem}.png"
    output_pdf_path = normalized_output_dir / f"{stem}.pdf"
    layout_sidecar_path = normalized_output_dir / f"{stem}.layout.json"
    render_result = _run_candidate_subprocess_renderer(
        runtime_template_root=runtime.template_path.parent,
        pack_root=runtime.pack_root,
        paper_root=normalized_output_dir,
        figure_id=figure_id,
        full_template_id=template_manifest.full_template_id,
        short_template_id=template_manifest.template_id,
        display_payload=display_payload,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )
    for path in (output_png_path, output_pdf_path, layout_sidecar_path):
        if not path.exists():
            raise FileNotFoundError(f"candidate display renderer did not write required artifact: {path}")
    return {
        "schema_version": 1,
        "status": "rendered",
        "candidate_only": True,
        "comparison_only": True,
        "publication_readiness_verdict": False,
        "repo_root": str(normalized_repo_root),
        "template_id": template_manifest.full_template_id,
        "short_template_id": template_manifest.template_id,
        "display_payload_path": str(payload_path),
        "candidate_entrypoint": "Rscript render_candidate.R --request {request_json}",
        "comparison_entrypoint": "Rscript render_candidate.R --request {request_json}",
        "default_renderer": {
            "renderer_family": template_manifest.renderer_family,
            "execution_mode": template_manifest.execution_mode,
            "entrypoint": template_manifest.entrypoint,
        },
        "authority_boundary": {
            "candidate_can_authorize_publication_readiness": False,
            "candidate_can_mutate_data_or_statistics": False,
            "candidate_can_replace_default_renderer": False,
            "comparison_receipt_can_authorize_publication_readiness": False,
            "comparison_receipt_can_replace_default_renderer": False,
            "default_renderer_promotion_already_landed": (
                template_manifest.renderer_family == "r_ggplot2"
                and template_manifest.execution_mode == "subprocess"
                and template_manifest.entrypoint == "Rscript render.R --request {request_json}"
            ),
        },
        "render_result": render_result,
        "rendered_artifacts": {
            "png_path": str(output_png_path),
            "pdf_path": str(output_pdf_path),
            "layout_sidecar_path": str(layout_sidecar_path),
            "png_ref": _workspace_ref(output_png_path, paper_root=normalized_output_dir),
            "pdf_ref": _workspace_ref(output_pdf_path, paper_root=normalized_output_dir),
            "layout_sidecar_ref": _workspace_ref(layout_sidecar_path, paper_root=normalized_output_dir),
            "png_sha256": _sha256_file(output_png_path),
            "pdf_sha256": _sha256_file(output_pdf_path),
            "layout_sidecar_sha256": _sha256_file(layout_sidecar_path),
        },
    }


__all__ = [
    "PUBLICATION_MANIFEST_BASENAME",
    "materialize_display_pack_publication_manifest",
    "render_display_pack_candidate_asset",
]
