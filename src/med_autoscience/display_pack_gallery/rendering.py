from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import os
import subprocess

from med_autoscience.display_pack_gallery_catalog import TemplateRecord
from med_autoscience.display_pack_subprocess_entrypoint import (
    expand_subprocess_entrypoint,
)
from med_autoscience.display_pack_gallery import paths
from med_autoscience.display_pack_gallery.assets import (
    RenderedAsset,
    _gallery_preview,
    _image_size,
    _relative_ref,
    _strip_trailing_whitespace,
    write_json,
)
from med_autoscience.display_pack_gallery.render_cache import (
    cache_hit,
    render_cache_key,
    write_render_cache,
)
from med_autoscience.display_pack_gallery.payloads import (
    _load_r_gallery_payload,
    _style_context_for,
)
from med_autoscience.display_pack_gallery.dependency_run_context import (
    load_gallery_dependency_run_context,
    required_profile_ids_for_record,
    validate_gallery_dependency_run_context,
)
from med_autoscience.display_pack_dependency_environment import apply_dependency_run_context

def _r_renderer_argv(record: TemplateRecord, request_path: Path) -> list[str]:
    return expand_subprocess_entrypoint(
        record.entrypoint,
        placeholders={
            "render_mode": "final",
            "request_json": str(request_path),
        },
    )


def _r_renderer_entrypoint_source(record: TemplateRecord) -> Path:
    for token in _r_renderer_argv(record, Path("gallery-render-request.json")):
        candidate = Path(token)
        if candidate.suffix.lower() == ".r":
            return candidate if candidate.is_absolute() else (record.template_dir / candidate).resolve()
    raise ValueError(f"R/ggplot2 template `{record.template_id}` entrypoint does not reference an R source file")


def _r_renderer_source_paths(record: TemplateRecord) -> list[Path]:
    rlib_root = paths.PACK_ROOT / "rlib" / "medicaldisplaycore"
    source_paths = [
        record.template_dir / "template.toml",
        paths.PACK_ROOT / "renderer_dependency_profile.json",
        *sorted(rlib_root.rglob("*.R")),
    ]
    if record.renderer_family == "r_ggplot2":
        source_paths.insert(0, _r_renderer_entrypoint_source(record))
    return source_paths


def _python_renderer_source_paths(record: TemplateRecord) -> list[Path]:
    source_paths = [
        record.template_dir / "template.toml",
        paths.PACK_ROOT / "src" / "fenggaolab_org_medical_display_core" / "illustration_shells" / "__init__.py",
        paths.PACK_ROOT / "src" / "fenggaolab_org_medical_display_core" / "illustration_shells" / "render_illustration_shell.py",
    ]
    if record.template_id == "submission_graphical_abstract":
        source_paths.append(paths.REPO_ROOT / "src" / "med_autoscience" / "display_pack_gallery" / "design_svg_renderer.py")
    return source_paths


def _rendered_r_asset(
    *,
    output_png: Path,
    output_pdf: Path,
    output_layout: Path,
    payload_path: Path,
    cache_status: str,
    cache_key: str,
    dependency_environment: dict[str, str] | None = None,
) -> RenderedAsset:
    preview_path, preview_size = _gallery_preview(output_png)
    return RenderedAsset(
        status="rendered",
        image_ref=_relative_ref(output_png),
        preview_image_ref=_relative_ref(preview_path),
        payload_ref=_relative_ref(payload_path),
        layout_ref=_relative_ref(output_layout),
        pdf_ref=_relative_ref(output_pdf),
        image_size_px=_image_size(output_png),
        preview_image_size_px=preview_size,
        render_cache_status=cache_status,
        render_cache_key=cache_key,
        dependency_environment=dependency_environment,
    )


def _read_render_cache_key(cache_path: Path) -> str:
    if not cache_path.is_file():
        return ""
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    value = payload.get("render_cache_key") if isinstance(payload, dict) else ""
    return value if isinstance(value, str) else ""


def _existing_r_template_asset(record: TemplateRecord, *, cache_status: str) -> RenderedAsset:
    payload_path = paths.ASSET_ROOT / f"{record.template_id}.payload.json"
    output_png = paths.ASSET_ROOT / f"{record.template_id}.png"
    output_pdf = paths.ASSET_ROOT / f"{record.template_id}.pdf"
    output_layout = paths.ASSET_ROOT / f"{record.template_id}.layout.json"
    cache_path = paths.ASSET_ROOT / f"{record.template_id}.render_cache.json"
    dependency_environment = _gallery_dependency_environment_for(record, allow_preview_without_run_context=True)
    required_outputs = (payload_path, output_png, output_pdf, output_layout)
    missing_outputs = [str(path) for path in required_outputs if not path.is_file()]
    if missing_outputs:
        return RenderedAsset(
            status="not_rendered",
            reason=f"package_only_missing_assets: {', '.join(missing_outputs)}",
            render_cache_status=cache_status,
            render_cache_key=_read_render_cache_key(cache_path),
            dependency_environment=dependency_environment,
        )
    return _rendered_r_asset(
        output_png=output_png,
        output_pdf=output_pdf,
        output_layout=output_layout,
        payload_path=payload_path,
        cache_status=cache_status,
        cache_key=_read_render_cache_key(cache_path),
        dependency_environment=dependency_environment,
    )


def _read_gallery_dependency_run_context() -> dict[str, Any]:
    return load_gallery_dependency_run_context(_gallery_dependency_run_context_path())


def _gallery_dependency_run_context_path() -> str:
    return str(os.environ.get("MAS_DISPLAY_GALLERY_DEPENDENCY_RUN_CONTEXT_PATH", "")).strip()


def _gallery_dependency_run_context_ref() -> str:
    return str(os.environ.get("MAS_DISPLAY_GALLERY_DEPENDENCY_RUN_CONTEXT_REF", "")).strip()


def _gallery_dependency_run_context_fingerprint() -> str:
    return str(os.environ.get("MAS_DISPLAY_GALLERY_DEPENDENCY_RUN_CONTEXT_FINGERPRINT", "")).strip()


def _r_subprocess_base_env() -> dict[str, str]:
    return {
        **dict(os.environ),
        "MAS_DISPLAY_OUTPUT_WIDTH_IN": "5",
        "MAS_DISPLAY_OUTPUT_HEIGHT_IN": "5",
    }


def _prepare_r_subprocess(argv: list[str]) -> tuple[list[str], dict[str, str]]:
    env = _r_subprocess_base_env()
    run_context = _read_gallery_dependency_run_context()
    if run_context:
        return apply_dependency_run_context(argv=argv, env=env, run_context=run_context)
    return argv, env


def _dependency_cache_context(dependency_environment: dict[str, str]) -> dict[str, str]:
    if dependency_environment.get("status") != "prepared":
        return dependency_environment
    run_context = _read_gallery_dependency_run_context()
    env_vars = run_context.get("env_vars") or run_context.get("environment_variables") or {}
    binary_paths = run_context.get("binary_paths") or {}
    return {
        **dependency_environment,
        "rscript_path": str(binary_paths.get("Rscript") or ""),
        "r_libs_user": str(env_vars.get("R_LIBS_USER") or run_context.get("managed_r_library_path") or ""),
    }


def _render_r_template(
    record: TemplateRecord,
    seed_payloads: dict[str, dict[str, Any]],
    *,
    force_render: bool = False,
) -> RenderedAsset:
    payload = _load_r_gallery_payload(record.template_id, seed_payloads)
    payload_path = paths.ASSET_ROOT / f"{record.template_id}.payload.json"
    output_png = paths.ASSET_ROOT / f"{record.template_id}.png"
    output_pdf = paths.ASSET_ROOT / f"{record.template_id}.pdf"
    output_layout = paths.ASSET_ROOT / f"{record.template_id}.layout.json"
    request_path = paths.ASSET_ROOT / f"{record.template_id}.render_request.json"
    request = {
        "schema_version": 1,
        "execution_mode": record.execution_mode,
        "renderer_family": record.renderer_family,
        "figure_id": record.template_id,
        "template_id": record.full_template_id,
        "short_template_id": record.template_id,
        "display_payload": payload,
        "output_png_path": str(output_png),
        "output_pdf_path": str(output_pdf),
        "layout_sidecar_path": str(output_layout),
    }
    dependency_environment = _gallery_dependency_environment_for(record)
    if dependency_environment:
        request["dependency_environment"] = dependency_environment
        request["dependency_cache_context"] = _dependency_cache_context(dependency_environment)
    cache_path = paths.ASSET_ROOT / f"{record.template_id}.render_cache.json"
    cache_key = render_cache_key(
        renderer="r_ggplot2_template",
        payload=payload,
        request=request,
        source_paths=_r_renderer_source_paths(record),
    )
    if not force_render and cache_hit(
        cache_path=cache_path,
        cache_key=cache_key,
        required_outputs=(payload_path, output_png, output_pdf, output_layout),
    ):
        return _rendered_r_asset(
            output_png=output_png,
            output_pdf=output_pdf,
            output_layout=output_layout,
            payload_path=payload_path,
            cache_status="hit",
            cache_key=cache_key,
            dependency_environment=dependency_environment,
        )
    write_json(payload_path, payload)
    write_json(request_path, request)
    argv, env = _prepare_r_subprocess(_r_renderer_argv(record, request_path))
    result = subprocess.run(
        argv,
        cwd=record.template_dir,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
        env=env,
    )
    request_path.unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"{record.template_id} render failed with code {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    for path in (output_png, output_pdf, output_layout):
        if not path.is_file():
            raise FileNotFoundError(f"{record.template_id} did not write {path}")
    write_render_cache(
        cache_path=cache_path,
        cache_key=cache_key,
        renderer="r_ggplot2_template",
    )
    return _rendered_r_asset(
        output_png=output_png,
        output_pdf=output_pdf,
        output_layout=output_layout,
        payload_path=payload_path,
        cache_status="miss",
        cache_key=cache_key,
        dependency_environment=dependency_environment,
    )


def _gallery_dependency_environment_for(
    record: TemplateRecord,
    *,
    allow_preview_without_run_context: bool = False,
) -> dict[str, str]:
    required_profile_ids = required_profile_ids_for_record(record)
    if not required_profile_ids:
        return {}
    run_context_path = _gallery_dependency_run_context_path()
    run_context_ref = _gallery_dependency_run_context_ref()
    run_context_fingerprint = _gallery_dependency_run_context_fingerprint()
    if not run_context_ref and run_context_path:
        run_context_ref = run_context_path
    if (not run_context_ref or not run_context_fingerprint) and allow_preview_without_run_context:
        return {
            "status": "gallery_preview",
            "run_context_ref": "gallery_preview:local_render_only",
            "run_context_fingerprint": "gallery-preview-not-publication-runtime-receipt",
        }
    if not run_context_ref or not run_context_fingerprint:
        missing = []
        if not run_context_ref:
            missing.append("MAS_DISPLAY_GALLERY_DEPENDENCY_RUN_CONTEXT_REF or PATH")
        if not run_context_fingerprint:
            missing.append("MAS_DISPLAY_GALLERY_DEPENDENCY_RUN_CONTEXT_FINGERPRINT")
        raise RuntimeError(
            f"{record.template_id} requires OPL-prepared dependency run-context for "
            f"{', '.join(required_profile_ids)}; missing {', '.join(missing)}. "
            "Run `opl runtime env prepare --domain mas --profile display --apply` or OPL doctor."
        )
    run_context = _read_gallery_dependency_run_context()
    validation = validate_gallery_dependency_run_context(
        record=record,
        run_context=run_context,
        expected_fingerprint=run_context_fingerprint,
    )
    return {
        "status": "prepared",
        "run_context_ref": run_context_ref,
        "run_context_fingerprint": validation["run_context_fingerprint"],
        "required_profile_ids": validation["required_profile_ids"],
    }


def _render_r_gallery_preview(
    record: TemplateRecord,
    seed_payloads: dict[str, dict[str, Any]],
    *,
    force_render: bool = False,
) -> RenderedAsset:
    payload = _load_r_gallery_payload(record.template_id, seed_payloads)
    payload_path = paths.ASSET_ROOT / f"{record.template_id}.payload.json"
    output_png = paths.ASSET_ROOT / f"{record.template_id}.png"
    output_pdf = paths.ASSET_ROOT / f"{record.template_id}.pdf"
    output_layout = paths.ASSET_ROOT / f"{record.template_id}.layout.json"
    request_path = paths.ASSET_ROOT / f"{record.template_id}.render_request.json"
    request = {
        "schema_version": 1,
        "execution_mode": "subprocess",
        "renderer_family": "r_ggplot2",
        "figure_id": record.template_id,
        "template_id": record.full_template_id,
        "short_template_id": record.template_id,
        "display_payload": payload,
        "output_png_path": str(output_png),
        "output_pdf_path": str(output_pdf),
        "layout_sidecar_path": str(output_layout),
        "gallery_preview_only": True,
    }
    dependency_environment = _gallery_dependency_environment_for(record)
    if dependency_environment:
        request["dependency_environment"] = dependency_environment
        request["dependency_cache_context"] = _dependency_cache_context(dependency_environment)
    cache_path = paths.ASSET_ROOT / f"{record.template_id}.render_cache.json"
    cache_key = render_cache_key(
        renderer="r_ggplot2_gallery_preview",
        payload=payload,
        request=request,
        source_paths=[
            *_r_renderer_source_paths(record),
        ],
    )
    if not force_render and cache_hit(
        cache_path=cache_path,
        cache_key=cache_key,
        required_outputs=(payload_path, output_png, output_pdf, output_layout),
    ):
        return _rendered_r_asset(
            output_png=output_png,
            output_pdf=output_pdf,
            output_layout=output_layout,
            payload_path=payload_path,
            cache_status="hit",
            cache_key=cache_key,
            dependency_environment=dependency_environment,
        )
    write_json(payload_path, payload)
    write_json(request_path, request)
    argv, env = _prepare_r_subprocess(
        [
            "Rscript",
            str(paths.PACK_ROOT / "rlib" / "medicaldisplaycore" / "evidence_renderer.R"),
            "--request",
            str(request_path),
        ]
    )
    result = subprocess.run(
        argv,
        cwd=paths.REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
        env=env,
    )
    request_path.unlink(missing_ok=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"{record.template_id} gallery preview failed with code {result.returncode}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    for path in (output_png, output_pdf, output_layout):
        if not path.is_file():
            raise FileNotFoundError(f"{record.template_id} did not write {path}")
    write_render_cache(
        cache_path=cache_path,
        cache_key=cache_key,
        renderer="r_ggplot2_gallery_preview",
    )
    return _rendered_r_asset(
        output_png=output_png,
        output_pdf=output_pdf,
        output_layout=output_layout,
        payload_path=payload_path,
        cache_status="miss",
        cache_key=cache_key,
        dependency_environment=dependency_environment,
    )


def _render_python_template(
    record: TemplateRecord,
    payload: dict[str, Any],
    *,
    output_root: Path,
    suffix: str,
    force_render: bool = False,
) -> RenderedAsset:
    output_root.mkdir(parents=True, exist_ok=True)
    output_png = output_root / f"{record.template_id}.{suffix}.png"
    output_pdf = output_root / f"{record.template_id}.{suffix}.pdf"
    output_svg = output_root / f"{record.template_id}.{suffix}.svg"
    output_layout = output_root / f"{record.template_id}.{suffix}.layout.json"
    payload_path = output_root / f"{record.template_id}.{suffix}.payload.json"
    render_payload = json.loads(json.dumps(payload))
    render_context = _style_context_for(record.template_id)
    if record.kind == "evidence_figure":
        raise RuntimeError("Python evidence templates are not retained in the current gallery")
    request = {
        "renderer_family": record.renderer_family,
        "kind": record.kind,
        "template_id": record.full_template_id,
        "short_template_id": record.template_id,
        "suffix": suffix,
        "render_context": render_context,
    }
    cache_path = output_root / f"{record.template_id}.{suffix}.render_cache.json"
    cache_key = render_cache_key(
        renderer="python_illustration_shell",
        payload=render_payload,
        request=request,
        source_paths=_python_renderer_source_paths(record),
    )
    if not force_render and cache_hit(
        cache_path=cache_path,
        cache_key=cache_key,
        required_outputs=(payload_path, output_png, output_layout),
    ):
        preview_path, preview_size = _gallery_preview(output_png)
        return RenderedAsset(
            status="rendered",
            image_ref=_relative_ref(output_png),
            preview_image_ref=_relative_ref(preview_path),
            payload_ref=_relative_ref(payload_path),
            layout_ref=_relative_ref(output_layout),
            pdf_ref=_relative_ref(output_pdf) if output_pdf.is_file() else "",
            svg_ref=_relative_ref(output_svg) if output_svg.is_file() else "",
            image_size_px=_image_size(output_png),
            preview_image_size_px=preview_size,
            render_cache_status="hit",
            render_cache_key=cache_key,
        )
    write_json(payload_path, render_payload)
    if record.kind == "illustration_shell":
        if record.template_id == "submission_graphical_abstract":
            from med_autoscience.display_pack_gallery.design_svg_renderer import (
                render_submission_graphical_abstract_gallery_preview,
            )

            render_submission_graphical_abstract_gallery_preview(
                shell_payload=render_payload,
                render_context=render_context,
                output_svg_path=output_svg,
                output_png_path=output_png,
                output_layout_path=output_layout,
            )
        else:
            from fenggaolab_org_medical_display_core.illustration_shells import render_illustration_shell

            render_illustration_shell(
                template_id=record.full_template_id,
                shell_payload=render_payload,
                render_context=render_context,
                output_svg_path=output_svg,
                output_png_path=output_png,
                output_pdf_path=output_pdf,
                output_layout_path=output_layout,
                payload_path=payload_path,
            )
    else:
        raise RuntimeError(f"unsupported python gallery kind `{record.kind}`")
    for path in (output_png, output_layout):
        if not path.is_file():
            raise FileNotFoundError(f"{record.template_id} did not write {path}")
    _strip_trailing_whitespace(output_svg)
    write_render_cache(
        cache_path=cache_path,
        cache_key=cache_key,
        renderer="python_illustration_shell",
    )
    preview_path, preview_size = _gallery_preview(output_png)
    return RenderedAsset(
        status="rendered",
        image_ref=_relative_ref(output_png),
        preview_image_ref=_relative_ref(preview_path),
        payload_ref=_relative_ref(payload_path),
        layout_ref=_relative_ref(output_layout),
        pdf_ref=_relative_ref(output_pdf) if output_pdf.is_file() else "",
        svg_ref=_relative_ref(output_svg) if output_svg.is_file() else "",
        image_size_px=_image_size(output_png),
        preview_image_size_px=preview_size,
        render_cache_status="miss",
        render_cache_key=cache_key,
    )


def _existing_python_template_asset(
    record: TemplateRecord,
    *,
    output_root: Path,
    suffix: str,
    cache_status: str,
) -> RenderedAsset:
    output_png = output_root / f"{record.template_id}.{suffix}.png"
    output_pdf = output_root / f"{record.template_id}.{suffix}.pdf"
    output_svg = output_root / f"{record.template_id}.{suffix}.svg"
    output_layout = output_root / f"{record.template_id}.{suffix}.layout.json"
    payload_path = output_root / f"{record.template_id}.{suffix}.payload.json"
    cache_path = output_root / f"{record.template_id}.{suffix}.render_cache.json"
    required_outputs = (payload_path, output_png, output_layout)
    missing_outputs = [str(path) for path in required_outputs if not path.is_file()]
    if missing_outputs:
        return RenderedAsset(
            status="not_rendered",
            reason=f"package_only_missing_assets: {', '.join(missing_outputs)}",
            render_cache_status=cache_status,
            render_cache_key=_read_render_cache_key(cache_path),
        )
    preview_path, preview_size = _gallery_preview(output_png)
    return RenderedAsset(
        status="rendered",
        image_ref=_relative_ref(output_png),
        preview_image_ref=_relative_ref(preview_path),
        payload_ref=_relative_ref(payload_path),
        layout_ref=_relative_ref(output_layout),
        pdf_ref=_relative_ref(output_pdf) if output_pdf.is_file() else "",
        svg_ref=_relative_ref(output_svg) if output_svg.is_file() else "",
        image_size_px=_image_size(output_png),
        preview_image_size_px=preview_size,
        render_cache_status=cache_status,
        render_cache_key=_read_render_cache_key(cache_path),
    )
