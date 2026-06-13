from __future__ import annotations

from .shared import Any, Path, _REPO_ROOT, _build_render_context, _paper_relative_path, _replace_catalog_entry, _require_namespaced_registry_id, _resolve_figure_catalog_id, display_layout_qc, display_pack_runtime, display_registry, dump_json, load_json, publication_display_contract
from .renderers import _prepare_python_illustration_output_paths


def _materialize_submission_graphical_abstract(
    *,
    paper_root: Path,
    figure_catalog: dict[str, Any],
    style_profile: publication_display_contract.PublicationStyleProfile,
    display_overrides: dict[tuple[str, str], publication_display_contract.DisplayOverride],
) -> tuple[str | None, list[str]]:
    submission_graphical_abstract_path = paper_root / "submission_graphical_abstract.json"
    if not submission_graphical_abstract_path.exists():
        return None, []

    spec = display_registry.get_illustration_shell_spec("submission_graphical_abstract")
    pack_id, _ = _require_namespaced_registry_id(spec.shell_id, label="submission_graphical_abstract shell_id")
    shell_payload = load_json(submission_graphical_abstract_path)
    figure_id = _resolve_figure_catalog_id(
        display_id=str(shell_payload.get("display_id") or ""),
        catalog_id=str(shell_payload.get("catalog_id") or ""),
    )
    render_context = _build_render_context(
        style_profile=style_profile,
        display_overrides=display_overrides,
        display_id=str(shell_payload.get("display_id") or ""),
        template_id=spec.shell_id,
    )
    output_svg_path = paper_root / "figures" / "generated" / f"{figure_id}_graphical_abstract.svg"
    output_png_path = paper_root / "figures" / "generated" / f"{figure_id}_graphical_abstract.png"
    output_layout_path = paper_root / "figures" / "generated" / f"{figure_id}_graphical_abstract.layout.json"
    _prepare_python_illustration_output_paths(
        output_png_path=output_png_path,
        output_svg_path=output_svg_path,
        layout_sidecar_path=output_layout_path,
    )
    render_callable = display_pack_runtime.load_python_plugin_callable(
        repo_root=_REPO_ROOT,
        template_id=spec.shell_id,
        paper_root=paper_root,
    )
    render_result = dict(
        render_callable(
            template_id=spec.shell_id,
            shell_payload=shell_payload,
            payload_path=submission_graphical_abstract_path,
            render_context=render_context,
            output_svg_path=output_svg_path,
            output_png_path=output_png_path,
            output_layout_path=output_layout_path,
        )
        or {}
    )
    layout_sidecar = load_json(output_layout_path)
    layout_sidecar["render_context"] = render_context
    dump_json(output_layout_path, layout_sidecar)
    qc_result = display_layout_qc.run_display_layout_qc(
        qc_profile=spec.shell_qc_profile,
        layout_sidecar=layout_sidecar,
    )
    qc_result["layout_sidecar_path"] = _paper_relative_path(output_layout_path, paper_root=paper_root)
    entry = {
        "figure_id": figure_id,
        "template_id": spec.shell_id,
        "pack_id": pack_id,
        "renderer_family": spec.renderer_family,
        "paper_role": str(shell_payload.get("paper_role") or spec.allowed_paper_roles[0]).strip(),
        "input_schema_id": spec.input_schema_id,
        "qc_profile": spec.shell_qc_profile,
        "qc_result": qc_result,
        "title": str(render_result.get("title") or shell_payload.get("title") or "").strip(),
        "caption": str(render_result.get("caption") or shell_payload.get("caption") or "").strip(),
        "export_paths": [
            _paper_relative_path(output_svg_path, paper_root=paper_root),
            _paper_relative_path(output_png_path, paper_root=paper_root),
        ],
        "source_paths": [
            _paper_relative_path(submission_graphical_abstract_path, paper_root=paper_root),
        ],
        "claim_ids": [],
        "render_context": render_context,
    }
    figure_catalog["figures"] = _replace_catalog_entry(
        list(figure_catalog.get("figures") or []),
        key="figure_id",
        value=figure_id,
        entry=entry,
    )
    return figure_id, [str(output_svg_path), str(output_png_path), str(output_layout_path)]


__all__ = [
    "_materialize_submission_graphical_abstract",
]
