from __future__ import annotations

from collections.abc import Mapping
import json
import os
from pathlib import Path
import re
import subprocess as _subprocess
import time
from types import SimpleNamespace
from typing import Any

from med_autoscience.display_pack_dependency_environment import (
    apply_dependency_run_context,
    load_dependency_run_context,
)
from med_autoscience.display_pack_subprocess_entrypoint import expand_subprocess_entrypoint

subprocess = SimpleNamespace(run=_subprocess.run)


def safe_artifact_stem(figure_id: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_.-]+", "_", figure_id.strip())
    if not normalized:
        raise ValueError("figure_id must produce a non-empty artifact stem")
    return normalized


def workspace_ref(path: Path, *, paper_root: Path) -> str:
    return path.resolve().relative_to(paper_root.resolve().parent).as_posix()


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def subprocess_placeholders(
    *,
    request_path: Path,
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
    figure_id: str,
    paper_root: Path,
    template_root: Path,
    pack_root: Path,
    render_mode: str,
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
        "render_mode": render_mode,
    }


def run_subprocess_renderer(
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
    dependency_environment: Mapping[str, Any] | None = None,
    request_short_template_id: str | None = None,
) -> dict[str, Any]:
    dependency_environment_payload = dict(dependency_environment or {})
    short_template_id = str(request_short_template_id or template_manifest.template_id).strip()
    if not short_template_id:
        raise ValueError("request_short_template_id must not be empty")
    request_dir = paper_root / "build" / "display_pack_render_requests"
    log_dir = paper_root / "build" / "display_pack_renderer_logs"
    request_path = request_dir / f"{safe_artifact_stem(figure_id)}.render_request.json"
    stdout_path = log_dir / f"{safe_artifact_stem(figure_id)}.stdout.txt"
    stderr_path = log_dir / f"{safe_artifact_stem(figure_id)}.stderr.txt"
    render_request = {
        "schema_version": 1,
        "execution_mode": "subprocess",
        "renderer_family": template_manifest.renderer_family,
        "figure_id": figure_id,
        "template_id": full_template_id,
        "short_template_id": short_template_id,
        "display_payload": dict(display_payload),
        "output_png_path": str(output_png_path),
        "output_pdf_path": str(output_pdf_path),
        "layout_sidecar_path": str(layout_sidecar_path),
        "dependency_environment": dependency_environment_payload,
    }
    write_json(request_path, render_request)
    placeholders = subprocess_placeholders(
        request_path=request_path,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
        figure_id=figure_id,
        paper_root=paper_root,
        template_root=runtime_template_root,
        pack_root=pack_root,
        render_mode="final",
    )
    argv = expand_subprocess_entrypoint(template_manifest.entrypoint, placeholders=placeholders)
    env = {
        **os.environ,
        "MAS_DISPLAY_RENDER_REQUEST": str(request_path),
        "MAS_DISPLAY_OUTPUT_PNG": str(output_png_path),
        "MAS_DISPLAY_OUTPUT_PDF": str(output_pdf_path),
        "MAS_DISPLAY_LAYOUT_SIDECAR": str(layout_sidecar_path),
        "MAS_DISPLAY_FIGURE_ID": figure_id,
        "MAS_DISPLAY_TEMPLATE_ID": full_template_id,
    }
    run_context: dict[str, Any] = {}
    if dependency_environment_payload:
        run_context = load_dependency_run_context(
            paper_root=paper_root,
            status=dependency_environment_payload,
        )
        argv, env = apply_dependency_run_context(argv=argv, env=env, run_context=run_context)
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
        "dependency_environment": dependency_environment_payload,
        "dependency_run_context": {
            "run_context_ref": str(dependency_environment_payload.get("run_context_ref") or ""),
            "execution_fingerprint": str(
                run_context.get("execution_fingerprint")
                or run_context.get("run_context_fingerprint")
                or dependency_environment_payload.get("run_context_fingerprint")
                or ""
            ),
        },
        "returncode": completed.returncode,
        "duration_seconds": duration_seconds,
        "request_path": str(request_path),
        "request_ref": workspace_ref(request_path, paper_root=paper_root),
        "stdout_path": str(stdout_path),
        "stdout_ref": workspace_ref(stdout_path, paper_root=paper_root),
        "stderr_path": str(stderr_path),
        "stderr_ref": workspace_ref(stderr_path, paper_root=paper_root),
    }
    if completed.returncode != 0:
        raise ValueError(
            f"subprocess display renderer failed for `{figure_id}` with return code "
            f"{completed.returncode}; stderr ref: {result['stderr_ref']}"
        )
    return result


def run_candidate_subprocess_renderer(
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
    request_path = request_dir / f"{safe_artifact_stem(figure_id)}.render_candidate_request.json"
    stdout_path = log_dir / f"{safe_artifact_stem(figure_id)}.stdout.txt"
    stderr_path = log_dir / f"{safe_artifact_stem(figure_id)}.stderr.txt"
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
    write_json(request_path, render_request)
    entrypoint = "Rscript render_candidate.R --request {request_json}"
    placeholders = subprocess_placeholders(
        request_path=request_path,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
        figure_id=figure_id,
        paper_root=paper_root,
        template_root=runtime_template_root,
        pack_root=pack_root,
        render_mode="candidate",
    )
    argv = expand_subprocess_entrypoint(entrypoint, placeholders=placeholders)
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
        "request_ref": workspace_ref(request_path, paper_root=paper_root),
        "stdout_path": str(stdout_path),
        "stdout_ref": workspace_ref(stdout_path, paper_root=paper_root),
        "stderr_path": str(stderr_path),
        "stderr_ref": workspace_ref(stderr_path, paper_root=paper_root),
    }
    if completed.returncode != 0:
        raise ValueError(
            f"candidate display renderer failed for `{figure_id}` with return code "
            f"{completed.returncode}; stderr ref: {result['stderr_ref']}"
        )
    return result


__all__ = [
    "expand_subprocess_entrypoint",
    "run_candidate_subprocess_renderer",
    "run_subprocess_renderer",
    "safe_artifact_stem",
    "subprocess_placeholders",
]
