from __future__ import annotations

from .shared import Any, Path, _ILLUSTRATION_DEFAULT_TEXT_BY_TEMPLATE_SHORT_ID, _ILLUSTRATION_OUTPUT_STEM_BY_TEMPLATE_SHORT_ID, _REPO_ROOT, _build_paper_surface_readmes, _build_render_context, _illustration_payload_path, _paper_relative_path, _prune_unreferenced_generated_surface_outputs, _replace_catalog_entry, _require_namespaced_registry_id, _resolve_figure_catalog_id, _resolve_illustration_shell_paper_role, _resolve_table_catalog_id, _table_payload_path, display_layout_qc, display_pack_lock, display_pack_runtime, display_registry, dump_json, get_template_short_id, load_json, publication_display_contract, utc_now, write_text
from .payload_loader import _load_evidence_display_payload
from .renderers import _load_layout_sidecar_or_raise, _prepare_python_illustration_output_paths, _prepare_python_render_output_paths, _prepare_table_shell_output_paths

def _iter_display_surface_entries(
    *,
    paper_root: Path,
    display_registry_payload: dict[str, Any],
    figure_catalog: dict[str, Any],
) -> list[dict[str, Any]]:
    display_items: list[dict[str, Any]] = []
    registered_display_ids: set[str] = set()
    registered_figure_ids: set[str] = set()

    for item in display_registry_payload.get("displays", []):
        if not isinstance(item, dict):
            raise ValueError("display_registry.json displays must contain objects")
        display_items.append(item)

        display_id = str(item.get("display_id") or "").strip()
        display_kind = str(item.get("display_kind") or "").strip()
        catalog_id = str(item.get("catalog_id") or "").strip()
        if display_id:
            registered_display_ids.add(display_id)
        if display_kind == "figure":
            figure_id = _resolve_figure_catalog_id(display_id=display_id, catalog_id=catalog_id)
            if figure_id:
                registered_figure_ids.add(figure_id)

    # Older paper lines can keep a valid illustration payload plus a stale figure
    # catalog entry even after the registry binding drifted away. Refresh those
    # catalog-only illustration entries through the normal materialization loop.
    for entry in figure_catalog.get("figures", []):
        if not isinstance(entry, dict):
            raise ValueError("figure_catalog.json figures must contain objects")
        template_id = str(entry.get("template_id") or "").strip()
        if not template_id or not display_registry.is_illustration_shell(template_id):
            continue

        spec = display_registry.get_illustration_shell_spec(template_id)
        if get_template_short_id(spec.shell_id) == "submission_graphical_abstract":
            continue

        figure_id = _resolve_figure_catalog_id(
            display_id=str(entry.get("display_id") or "").strip(),
            catalog_id=str(entry.get("figure_id") or entry.get("catalog_id") or "").strip(),
        )
        if not figure_id or figure_id in registered_figure_ids:
            continue

        payload_path = _illustration_payload_path(paper_root=paper_root, input_schema_id=spec.input_schema_id)
        if not payload_path.exists():
            continue

        shell_payload = load_json(payload_path)
        display_id = str(shell_payload.get("display_id") or entry.get("display_id") or "").strip()
        if not display_id or display_id in registered_display_ids:
            continue

        display_items.append(
            {
                "display_id": display_id,
                "display_kind": "figure",
                "requirement_key": spec.shell_id,
                "catalog_id": figure_id,
            }
        )
        registered_display_ids.add(display_id)
        registered_figure_ids.add(figure_id)

    return display_items

def materialize_display_surface(*, paper_root: Path) -> dict[str, Any]:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    display_registry_payload = load_json(resolved_paper_root / "display_registry.json")
    figure_catalog = load_json(resolved_paper_root / "figures" / "figure_catalog.json")
    table_catalog = load_json(resolved_paper_root / "tables" / "table_catalog.json")
    style_profile: publication_display_contract.PublicationStyleProfile | None = None
    display_overrides: dict[tuple[str, str], publication_display_contract.DisplayOverride] | None = None

    figures_materialized: list[str] = []
    tables_materialized: list[str] = []
    written_files: list[str] = publication_display_contract.seed_publication_display_contracts_if_missing(
        paper_root=resolved_paper_root
    )

    for item in _iter_display_surface_entries(
        paper_root=resolved_paper_root,
        display_registry_payload=display_registry_payload,
        figure_catalog=figure_catalog,
    ):
        requirement_key = str(item.get("requirement_key") or "").strip()
        display_id = str(item.get("display_id") or "").strip()
        display_kind = str(item.get("display_kind") or "").strip()
        catalog_id = str(item.get("catalog_id") or "").strip()
        requirement_short_id = ""
        if display_kind == "figure":
            if display_registry.is_illustration_shell(requirement_key):
                requirement_short_id = get_template_short_id(
                    display_registry.get_illustration_shell_spec(requirement_key).shell_id
                )
            elif display_registry.is_evidence_figure_template(requirement_key):
                requirement_short_id = get_template_short_id(
                    display_registry.get_evidence_figure_spec(requirement_key).template_id
                )
        elif display_kind == "table" and display_registry.is_table_shell(requirement_key):
            requirement_short_id = get_template_short_id(display_registry.get_table_shell_spec(requirement_key).shell_id)

        if (
            display_kind == "figure"
            and display_registry.is_illustration_shell(requirement_key)
            and requirement_short_id != "submission_graphical_abstract"
        ):
            spec = display_registry.get_illustration_shell_spec(requirement_key)
            pack_id, template_short_id = _require_namespaced_registry_id(
                spec.shell_id,
                label=f"{requirement_key} shell_id",
            )
            output_stem = _ILLUSTRATION_OUTPUT_STEM_BY_TEMPLATE_SHORT_ID.get(template_short_id)
            if output_stem is None:
                raise ValueError(f"unsupported illustration shell output stem for `{spec.shell_id}`")
            default_title, default_caption = _ILLUSTRATION_DEFAULT_TEXT_BY_TEMPLATE_SHORT_ID.get(
                template_short_id,
                ("", ""),
            )
            if style_profile is None:
                style_profile = publication_display_contract.load_publication_style_profile(
                    resolved_paper_root / "publication_style_profile.json"
                )
            if display_overrides is None:
                display_overrides = publication_display_contract.load_display_overrides(
                    resolved_paper_root / "display_overrides.json"
                )
            render_context = _build_render_context(
                style_profile=style_profile,
                display_overrides=display_overrides,
                display_id=display_id,
                template_id=spec.shell_id,
            )
            payload_path = _illustration_payload_path(
                paper_root=resolved_paper_root,
                input_schema_id=spec.input_schema_id,
            )
            shell_payload = load_json(payload_path)
            paper_role = _resolve_illustration_shell_paper_role(
                shell_payload=shell_payload,
                requirement_key=requirement_key,
                allowed_paper_roles=spec.allowed_paper_roles,
            )
            if paper_role not in spec.allowed_paper_roles:
                allowed_roles = ", ".join(spec.allowed_paper_roles)
                raise ValueError(
                    f"display `{display_id}` paper_role `{paper_role}` is not allowed for illustration shell `{spec.shell_id}`; "
                    f"allowed: {allowed_roles}"
                )
            figure_id = _resolve_figure_catalog_id(display_id=display_id, catalog_id=catalog_id)
            output_svg_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_{output_stem}.svg"
            output_png_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_{output_stem}.png"
            output_layout_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_{output_stem}.layout.json"
            _prepare_python_illustration_output_paths(
                output_png_path=output_png_path,
                output_svg_path=output_svg_path,
                layout_sidecar_path=output_layout_path,
            )
            render_callable = display_pack_runtime.load_python_plugin_callable(
                repo_root=_REPO_ROOT,
                template_id=spec.shell_id,
                paper_root=resolved_paper_root,
            )
            render_result = dict(
                render_callable(
                    template_id=spec.shell_id,
                    shell_payload=shell_payload,
                    payload_path=payload_path,
                    render_context=render_context,
                    output_svg_path=output_svg_path,
                    output_png_path=output_png_path,
                    output_layout_path=output_layout_path,
                )
                or {}
            )
            layout_sidecar = _load_layout_sidecar_or_raise(path=output_layout_path, template_id=spec.shell_id)
            layout_sidecar["render_context"] = render_context
            dump_json(output_layout_path, layout_sidecar)
            qc_result = display_layout_qc.run_display_layout_qc(
                qc_profile=spec.shell_qc_profile,
                layout_sidecar=layout_sidecar,
            )
            qc_result["layout_sidecar_path"] = _paper_relative_path(output_layout_path, paper_root=resolved_paper_root)
            written_files.extend([str(output_svg_path), str(output_png_path), str(output_layout_path)])
            entry = {
                "figure_id": figure_id,
                "template_id": spec.shell_id,
                "pack_id": pack_id,
                "renderer_family": spec.renderer_family,
                "paper_role": paper_role,
                "input_schema_id": spec.input_schema_id,
                "qc_profile": spec.shell_qc_profile,
                "qc_result": qc_result,
                "title": str(render_result.get("title") or shell_payload.get("title") or default_title).strip()
                or default_title,
                "caption": str(render_result.get("caption") or shell_payload.get("caption") or default_caption).strip(),
                "export_paths": [
                    _paper_relative_path(output_svg_path, paper_root=resolved_paper_root),
                    _paper_relative_path(output_png_path, paper_root=resolved_paper_root),
                ],
                "source_paths": [
                    _paper_relative_path(payload_path, paper_root=resolved_paper_root),
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
            figures_materialized.append(figure_id)
            continue

        if requirement_short_id == "table1_baseline_characteristics":
            if display_kind != "table":
                raise ValueError("table1_baseline_characteristics must be registered as a table display")
            spec = display_registry.get_table_shell_spec(requirement_key)
            pack_id, _ = _require_namespaced_registry_id(spec.shell_id, label="table1_baseline_characteristics shell_id")
            payload_path = _table_payload_path(paper_root=resolved_paper_root, input_schema_id=spec.input_schema_id)
            payload = load_json(payload_path)
            table_id = _resolve_table_catalog_id(display_id=display_id, catalog_id=catalog_id)
            output_csv_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_baseline_characteristics.csv"
            output_md_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_baseline_characteristics.md"
            _prepare_table_shell_output_paths(
                output_md_path=output_md_path,
                output_csv_path=output_csv_path,
            )
            render_callable = display_pack_runtime.load_python_plugin_callable(
                repo_root=_REPO_ROOT,
                template_id=spec.shell_id,
                paper_root=resolved_paper_root,
            )
            render_result = dict(
                render_callable(
                    template_id=spec.shell_id,
                    payload_path=payload_path,
                    payload=payload,
                    output_md_path=output_md_path,
                    output_csv_path=output_csv_path,
                )
                or {}
            )
            written_files.extend([str(output_csv_path), str(output_md_path)])
            entry = {
                "table_id": table_id,
                "table_shell_id": spec.shell_id,
                "pack_id": pack_id,
                "paper_role": spec.allowed_paper_roles[0],
                "input_schema_id": spec.input_schema_id,
                "qc_profile": spec.table_qc_profile,
                "qc_result": {
                    "status": "pass",
                    "issues": [],
                    "checked_at": utc_now(),
                },
                "title": str(render_result.get("title") or "Baseline characteristics").strip() or "Baseline characteristics",
                "caption": str(
                    render_result.get("caption") or "Baseline characteristics across prespecified groups."
                ).strip(),
                "asset_paths": [
                    _paper_relative_path(output_csv_path, paper_root=resolved_paper_root),
                    _paper_relative_path(output_md_path, paper_root=resolved_paper_root),
                ],
                "source_paths": [
                    _paper_relative_path(payload_path, paper_root=resolved_paper_root),
                ],
                "claim_ids": [],
            }
            table_catalog["tables"] = _replace_catalog_entry(
                list(table_catalog.get("tables") or []),
                key="table_id",
                value=table_id,
                entry=entry,
            )
            tables_materialized.append(table_id)
            continue

        if requirement_short_id in {
            "table2_time_to_event_performance_summary",
            "table3_clinical_interpretation_summary",
            "performance_summary_table_generic",
            "grouped_risk_event_summary_table",
        }:
            if display_kind != "table":
                raise ValueError(f"{requirement_key} must be registered as a table display")
            spec = display_registry.get_table_shell_spec(requirement_key)
            pack_id, _ = _require_namespaced_registry_id(spec.shell_id, label=f"{requirement_key} shell_id")
            payload_path = _table_payload_path(paper_root=resolved_paper_root, input_schema_id=spec.input_schema_id)
            payload = load_json(payload_path)
            table_id = _resolve_table_catalog_id(display_id=display_id, catalog_id=catalog_id)
            output_csv_path: Path | None = None
            if requirement_short_id == "table2_time_to_event_performance_summary":
                output_md_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_time_to_event_performance_summary.md"
                default_title = "Time-to-event model performance summary"
                default_caption = "Time-to-event discrimination and error metrics across analysis cohorts."
            elif requirement_short_id == "table3_clinical_interpretation_summary":
                output_md_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_clinical_interpretation_summary.md"
                default_title = "Clinical interpretation summary"
                default_caption = "Clinical interpretation anchors for prespecified risk groups and use cases."
            elif requirement_short_id == "performance_summary_table_generic":
                output_md_path = (
                    resolved_paper_root / "tables" / "generated" / f"{table_id}_performance_summary_table_generic.md"
                )
                output_csv_path = (
                    resolved_paper_root / "tables" / "generated" / f"{table_id}_performance_summary_table_generic.csv"
                )
                default_title = "Performance summary"
                default_caption = "Structured repeated-validation performance summaries across candidate packages."
            else:
                output_md_path = (
                    resolved_paper_root / "tables" / "generated" / f"{table_id}_grouped_risk_event_summary_table.md"
                )
                output_csv_path = (
                    resolved_paper_root / "tables" / "generated" / f"{table_id}_grouped_risk_event_summary_table.csv"
                )
                default_title = "Grouped risk event summary"
                default_caption = "Observed case counts, event counts, and absolute risks across grouped-risk strata."
            _prepare_table_shell_output_paths(
                output_md_path=output_md_path,
                output_csv_path=output_csv_path,
            )
            render_callable = display_pack_runtime.load_python_plugin_callable(
                repo_root=_REPO_ROOT,
                template_id=spec.shell_id,
                paper_root=resolved_paper_root,
            )
            render_result = dict(
                render_callable(
                    template_id=spec.shell_id,
                    payload_path=payload_path,
                    payload=payload,
                    output_md_path=output_md_path,
                    output_csv_path=output_csv_path,
                )
                or {}
            )
            written_files.append(str(output_md_path))
            if output_csv_path is not None:
                written_files.append(str(output_csv_path))
            entry = {
                "table_id": table_id,
                "table_shell_id": spec.shell_id,
                "pack_id": pack_id,
                "paper_role": spec.allowed_paper_roles[0],
                "input_schema_id": spec.input_schema_id,
                "qc_profile": spec.table_qc_profile,
                "qc_result": {
                    "status": "pass",
                    "issues": [],
                    "checked_at": utc_now(),
                },
                "title": str(render_result.get("title") or default_title).strip() or default_title,
                "caption": str(render_result.get("caption") or default_caption).strip(),
                "asset_paths": [
                    *(
                        [_paper_relative_path(output_csv_path, paper_root=resolved_paper_root)]
                        if output_csv_path is not None
                        else []
                    ),
                    _paper_relative_path(output_md_path, paper_root=resolved_paper_root),
                ],
                "source_paths": [
                    _paper_relative_path(payload_path, paper_root=resolved_paper_root),
                ],
                "claim_ids": [],
            }
            table_catalog["tables"] = _replace_catalog_entry(
                list(table_catalog.get("tables") or []),
                key="table_id",
                value=table_id,
                entry=entry,
            )
            tables_materialized.append(table_id)
            continue

        if display_kind == "figure" and display_registry.is_evidence_figure_template(requirement_key):
            spec = display_registry.get_evidence_figure_spec(requirement_key)
            pack_id, template_short_id = _require_namespaced_registry_id(spec.template_id, label=f"{requirement_key} template_id")
            if style_profile is None:
                style_profile = publication_display_contract.load_publication_style_profile(
                    resolved_paper_root / "publication_style_profile.json"
                )
            if display_overrides is None:
                display_overrides = publication_display_contract.load_display_overrides(
                    resolved_paper_root / "display_overrides.json"
                )
            figure_id = _resolve_figure_catalog_id(display_id=display_id, catalog_id=catalog_id)
            payload_path, display_payload = _load_evidence_display_payload(
                paper_root=resolved_paper_root,
                spec=spec,
                display_id=display_id,
            )
            render_context = _build_render_context(
                style_profile=style_profile,
                display_overrides=display_overrides,
                display_id=display_id,
                template_id=spec.template_id,
            )
            render_payload = dict(display_payload)
            render_payload["render_context"] = render_context
            output_png_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_{template_short_id}.png"
            output_pdf_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_{template_short_id}.pdf"
            layout_sidecar_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_{template_short_id}.layout.json"
            _prepare_python_render_output_paths(
                output_png_path=output_png_path,
                output_pdf_path=output_pdf_path,
                layout_sidecar_path=layout_sidecar_path,
            )
            render_callable = display_pack_runtime.load_python_plugin_callable(
                repo_root=_REPO_ROOT,
                template_id=spec.template_id,
                paper_root=resolved_paper_root,
            )
            render_callable(
                template_id=spec.template_id,
                display_payload=render_payload,
                output_png_path=output_png_path,
                output_pdf_path=output_pdf_path,
                layout_sidecar_path=layout_sidecar_path,
            )
            layout_sidecar = _load_layout_sidecar_or_raise(path=layout_sidecar_path, template_id=spec.template_id)
            layout_sidecar["render_context"] = render_context
            dump_json(layout_sidecar_path, layout_sidecar)
            qc_result = display_layout_qc.run_display_layout_qc(
                qc_profile=spec.layout_qc_profile,
                layout_sidecar=layout_sidecar,
            )
            qc_result["layout_sidecar_path"] = _paper_relative_path(layout_sidecar_path, paper_root=resolved_paper_root)
            written_files.extend([str(output_png_path), str(output_pdf_path), str(layout_sidecar_path)])
            paper_role = str(display_payload.get("paper_role") or spec.allowed_paper_roles[0]).strip()
            if paper_role not in spec.allowed_paper_roles:
                allowed_roles = ", ".join(spec.allowed_paper_roles)
                raise ValueError(
                    f"display `{display_id}` paper_role `{paper_role}` is not allowed for template `{spec.template_id}`; "
                    f"allowed: {allowed_roles}"
                )
            entry = {
                "figure_id": figure_id,
                "template_id": spec.template_id,
                "pack_id": pack_id,
                "renderer_family": spec.renderer_family,
                "paper_role": paper_role,
                "input_schema_id": spec.input_schema_id,
                "qc_profile": spec.layout_qc_profile,
                "qc_result": qc_result,
                "title": str(display_payload.get("title") or "").strip(),
                "caption": str(display_payload.get("caption") or "").strip(),
                "export_paths": [
                    _paper_relative_path(output_png_path, paper_root=resolved_paper_root),
                    _paper_relative_path(output_pdf_path, paper_root=resolved_paper_root),
                ],
                "source_paths": [
                    _paper_relative_path(payload_path, paper_root=resolved_paper_root),
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
            figures_materialized.append(figure_id)
            continue

    submission_graphical_abstract_path = resolved_paper_root / "submission_graphical_abstract.json"
    if submission_graphical_abstract_path.exists():
        spec = display_registry.get_illustration_shell_spec("submission_graphical_abstract")
        pack_id, _ = _require_namespaced_registry_id(spec.shell_id, label="submission_graphical_abstract shell_id")
        if style_profile is None:
            style_profile = publication_display_contract.load_publication_style_profile(
                resolved_paper_root / "publication_style_profile.json"
            )
        if display_overrides is None:
            display_overrides = publication_display_contract.load_display_overrides(
                resolved_paper_root / "display_overrides.json"
            )
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
        output_svg_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_graphical_abstract.svg"
        output_png_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_graphical_abstract.png"
        output_layout_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_graphical_abstract.layout.json"
        _prepare_python_illustration_output_paths(
            output_png_path=output_png_path,
            output_svg_path=output_svg_path,
            layout_sidecar_path=output_layout_path,
        )
        render_callable = display_pack_runtime.load_python_plugin_callable(
            repo_root=_REPO_ROOT,
            template_id=spec.shell_id,
            paper_root=resolved_paper_root,
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
        qc_result["layout_sidecar_path"] = _paper_relative_path(output_layout_path, paper_root=resolved_paper_root)
        written_files.extend([str(output_svg_path), str(output_png_path), str(output_layout_path)])
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
                _paper_relative_path(output_svg_path, paper_root=resolved_paper_root),
                _paper_relative_path(output_png_path, paper_root=resolved_paper_root),
            ],
            "source_paths": [
                _paper_relative_path(submission_graphical_abstract_path, paper_root=resolved_paper_root),
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
        if figure_id not in figures_materialized:
            figures_materialized.append(figure_id)

    pruned_generated_paths = _prune_unreferenced_generated_surface_outputs(
        paper_root=resolved_paper_root,
        figure_catalog=figure_catalog,
        table_catalog=table_catalog,
    )
    readme_paths: list[str] = []
    for path, content in _build_paper_surface_readmes(
        paper_root=resolved_paper_root,
        figure_catalog=figure_catalog,
        table_catalog=table_catalog,
    ).items():
        write_text(path, content)
        readme_paths.append(str(path))
    dump_json(resolved_paper_root / "figures" / "figure_catalog.json", figure_catalog)
    dump_json(resolved_paper_root / "tables" / "table_catalog.json", table_catalog)
    display_pack_lock_path = display_pack_lock.write_display_pack_lock(
        paper_root=resolved_paper_root,
        repo_root=_REPO_ROOT,
    )
    written_files.extend(
        [
            str(resolved_paper_root / "figures" / "figure_catalog.json"),
            str(resolved_paper_root / "tables" / "table_catalog.json"),
            str(display_pack_lock_path),
            *readme_paths,
        ]
    )
    return {
        "status": "materialized",
        "paper_root": str(resolved_paper_root),
        "figures_materialized": figures_materialized,
        "tables_materialized": tables_materialized,
        "pruned_generated_paths": pruned_generated_paths,
        "written_files": written_files,
    }


__all__ = [
    "_iter_display_surface_entries",
    "materialize_display_surface",
]
