from __future__ import annotations

from med_autoscience.display_pack_e2e_runtime import _run_subprocess_renderer
from med_autoscience.display_pack_dependency_environment import (
    dependency_environment_finding,
    dependency_environment_status,
)

from med_autoscience.controllers import display_pack_surface_sync

from .shared import Any, Path, _ILLUSTRATION_DEFAULT_TEXT_BY_TEMPLATE_SHORT_ID, _ILLUSTRATION_OUTPUT_STEM_BY_TEMPLATE_SHORT_ID, _REPO_ROOT, _build_paper_surface_readmes, _build_render_context, _evidence_payload_path, _illustration_payload_path, _paper_relative_path, _prune_unreferenced_generated_surface_outputs, _replace_catalog_entry, _require_namespaced_registry_id, _resolve_figure_catalog_id, _resolve_illustration_shell_paper_role, _resolve_table_catalog_id, _table_payload_path, display_layout_qc, display_pack_lock, display_pack_runtime, display_registry, dump_json, get_template_short_id, load_json, publication_display_contract, utc_now, write_text
from .materialize_parts.contract_figures import _materialize_contract_backed_figure
from .materialize_parts.visual_audit import _write_catalog_visual_audit_receipt, materialize_display_visual_audit
from .materialize_parts.workspace import _active_generated_illustration_paths_from_catalog, _claim_ids_for_table, _is_known_requirement_key, _load_display_shell_payload, _purpose_first_renderer_fields, _resolve_contract_backed_figure_contract_path, _resolve_requirement_key_from_shell
from .payload_loader import _load_evidence_display_payload
from .renderers import _load_layout_sidecar_or_raise, _prepare_python_illustration_output_paths, _prepare_python_render_output_paths, _prepare_table_shell_output_paths
from .source_hydration import hydrate_display_surface_sources_from_current_body
from .submission_graphical_abstract import _materialize_submission_graphical_abstract
from .validation_tables import _validate_cohort_flow_payload


def _render_evidence_figure_by_template_runtime(
    *,
    template_id: str,
    display_payload: dict[str, Any],
    paper_root: Path,
    figure_id: str,
    output_png_path: Path,
    output_pdf_path: Path,
    layout_sidecar_path: Path,
    output_svg_path: Path | None = None,
) -> dict[str, Any]:
    _, requested_template_short_id = _require_namespaced_registry_id(
        template_id,
        label=f"{template_id} template_id",
    )
    runtime = display_pack_runtime.resolve_display_template_runtime(
        repo_root=_REPO_ROOT,
        template_id=template_id,
        paper_root=paper_root,
    )
    template_manifest = runtime.template_manifest
    if template_manifest.renderer_family != "r_ggplot2":
        raise ValueError(
            f"evidence figure template `{template_id}` must use r_ggplot2; "
            f"observed renderer `{template_manifest.renderer_family}`"
        )
    if template_manifest.execution_mode != "subprocess":
        raise ValueError(
            f"evidence figure template `{template_id}` must use subprocess execution mode; "
            f"observed `{template_manifest.execution_mode}`"
        )
    if output_svg_path is not None:
        raise ValueError(f"subprocess evidence figure template `{template_id}` cannot export svg from this materializer")
    return _run_subprocess_renderer(
        runtime_template_root=runtime.template_path.parent,
        pack_root=runtime.pack_root,
        template_manifest=template_manifest,
        paper_root=paper_root,
        figure_id=figure_id,
        full_template_id=template_manifest.full_template_id,
        display_payload=display_payload,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
        request_short_template_id=requested_template_short_id,
    )


def _render_illustration_shell_by_template_runtime(
    *,
    template_id: str,
    shell_payload: dict[str, Any],
    render_context: dict[str, Any],
    payload_path: Path,
    paper_root: Path,
    figure_id: str,
    output_png_path: Path,
    output_pdf_path: Path | None,
    output_svg_path: Path,
    output_layout_path: Path,
    dependency_environment: dict[str, Any] | None = None,
) -> dict[str, Any]:
    runtime = display_pack_runtime.resolve_display_template_runtime(
        repo_root=_REPO_ROOT,
        template_id=template_id,
        paper_root=paper_root,
    )
    template_manifest = runtime.template_manifest
    if template_manifest.execution_mode == "subprocess":
        if output_pdf_path is None:
            raise ValueError(f"subprocess illustration shell `{template_id}` requires a PDF export path")
        template_short_id = get_template_short_id(template_id)
        display_payload = (
            _validate_cohort_flow_payload(payload_path, dict(shell_payload))
            if template_short_id == "cohort_flow_figure"
            else dict(shell_payload)
        )
        display_payload["render_context"] = render_context
        result = _run_subprocess_renderer(
            runtime_template_root=runtime.template_path.parent,
            pack_root=runtime.pack_root,
            template_manifest=template_manifest,
            paper_root=paper_root,
            figure_id=figure_id,
            full_template_id=template_manifest.full_template_id,
            display_payload=display_payload,
            output_png_path=output_png_path,
            output_pdf_path=output_pdf_path,
            layout_sidecar_path=output_layout_path,
            dependency_environment=dependency_environment,
        )
        if "svg" in template_manifest.required_exports and not output_svg_path.exists():
            raise ValueError(f"subprocess illustration shell `{template_id}` did not write requested svg export")
        return result
    if template_manifest.execution_mode != "python_plugin":
        raise ValueError(
            f"illustration shell `{template_id}` uses unsupported execution mode `{template_manifest.execution_mode}`"
        )
    _prepare_python_illustration_output_paths(
        output_png_path=output_png_path,
        output_svg_path=output_svg_path,
        layout_sidecar_path=output_layout_path,
    )
    if output_pdf_path is not None:
        output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    render_callable = display_pack_runtime.load_python_plugin_callable(
        repo_root=_REPO_ROOT,
        template_id=template_id,
        paper_root=paper_root,
    )
    render_kwargs = {
        "template_id": template_id,
        "shell_payload": shell_payload,
        "payload_path": payload_path,
        "render_context": render_context,
        "output_svg_path": output_svg_path,
        "output_png_path": output_png_path,
        "output_layout_path": output_layout_path,
    }
    if output_pdf_path is not None:
        render_kwargs["output_pdf_path"] = output_pdf_path
    return dict(render_callable(**render_kwargs) or {})


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
    source_hydration_result = hydrate_display_surface_sources_from_current_body(
        paper_root=resolved_paper_root,
        display_registry_payload=display_registry_payload,
    )
    figure_catalog = load_json(resolved_paper_root / "figures" / "figure_catalog.json")
    table_catalog = load_json(resolved_paper_root / "tables" / "table_catalog.json")
    claim_evidence_map_path = resolved_paper_root / "claim_evidence_map.json"
    claim_evidence_map = load_json(claim_evidence_map_path) if claim_evidence_map_path.exists() else {}
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
        registry_requirement_key = requirement_key
        shell_payload = _load_display_shell_payload(paper_root=resolved_paper_root, item=item)
        requirement_key = _resolve_requirement_key_from_shell(
            requirement_key=requirement_key,
            shell_payload=shell_payload,
        )
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

        contract_path = None
        if (
            display_kind == "figure"
            and shell_payload
        ):
            contract_path = _resolve_contract_backed_figure_contract_path(
                paper_root=resolved_paper_root,
                item=item,
                shell_payload=shell_payload,
            )
        if contract_path is not None:
            figure_id, contract_written_files = _materialize_contract_backed_figure(
                paper_root=resolved_paper_root,
                item=item,
                shell_payload=shell_payload,
                contract_path=contract_path,
                figure_catalog=figure_catalog,
            )
            written_files.extend(contract_written_files)
            figures_materialized.append(figure_id)
            continue

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
                registry_item=item,
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
            active_paths = _active_generated_illustration_paths_from_catalog(
                paper_root=resolved_paper_root,
                figure_catalog=figure_catalog,
                figure_id=figure_id,
                template_id=spec.shell_id,
                pdf_required="pdf" in spec.required_exports,
            )
            if active_paths is None:
                output_png_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_{output_stem}.png"
                output_pdf_path = (
                    resolved_paper_root / "figures" / "generated" / f"{figure_id}_{output_stem}.pdf"
                    if "pdf" in spec.required_exports
                    else None
                )
                output_layout_path = (
                    resolved_paper_root / "figures" / "generated" / f"{figure_id}_{output_stem}.layout.json"
                )
            else:
                output_png_path, output_pdf_path, output_layout_path = active_paths
            output_svg_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_{output_stem}.svg"
            dependency_environment = dependency_environment_status(
                repo_root=_REPO_ROOT,
                paper_root=resolved_paper_root,
                records=[
                    display_pack_runtime.resolve_display_template_runtime(
                        repo_root=_REPO_ROOT,
                        template_id=spec.shell_id,
                        paper_root=resolved_paper_root,
                    )
                ],
            )
            dependency_finding = dependency_environment_finding(dependency_environment)
            if dependency_finding is not None:
                raise ValueError(
                    f"display shell `{figure_id}` dependency environment is not prepared; "
                    f"route: {dependency_finding['route_hint']}; "
                    f"reason: {dependency_environment.get('blocker_reason') or dependency_environment.get('status')}"
                )
            preexisting_svg_mtime = output_svg_path.stat().st_mtime if output_svg_path.exists() else None
            render_result = _render_illustration_shell_by_template_runtime(
                template_id=spec.shell_id,
                shell_payload=shell_payload,
                render_context=render_context,
                payload_path=payload_path,
                paper_root=resolved_paper_root,
                figure_id=figure_id,
                output_png_path=output_png_path,
                output_pdf_path=output_pdf_path,
                output_svg_path=output_svg_path,
                output_layout_path=output_layout_path,
                dependency_environment=dependency_environment,
            )
            layout_sidecar = _load_layout_sidecar_or_raise(path=output_layout_path, template_id=spec.shell_id)
            layout_sidecar["render_context"] = render_context
            dump_json(output_layout_path, layout_sidecar)
            qc_result = display_layout_qc.run_display_layout_qc(
                qc_profile=spec.shell_qc_profile,
                layout_sidecar=layout_sidecar,
            )
            qc_result["layout_sidecar_path"] = _paper_relative_path(output_layout_path, paper_root=resolved_paper_root)
            export_paths = [
                _paper_relative_path(output_png_path, paper_root=resolved_paper_root),
            ]
            written_output_paths = [str(output_png_path), str(output_layout_path)]
            svg_was_generated = (
                output_svg_path.exists()
                and (preexisting_svg_mtime is None or output_svg_path.stat().st_mtime != preexisting_svg_mtime)
            )
            if svg_was_generated:
                export_paths.insert(0, _paper_relative_path(output_svg_path, paper_root=resolved_paper_root))
                written_output_paths.append(str(output_svg_path))
            if output_pdf_path is not None:
                export_paths.append(_paper_relative_path(output_pdf_path, paper_root=resolved_paper_root))
                written_output_paths.append(str(output_pdf_path))
            written_files.extend(written_output_paths)
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
                "export_paths": export_paths,
                "source_paths": [
                    _paper_relative_path(payload_path, paper_root=resolved_paper_root),
                ],
                "claim_ids": [],
                "render_context": render_context,
            }
            entry.update(_purpose_first_renderer_fields(layout_sidecar))
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
            claim_ids = _claim_ids_for_table(
                table_catalog=table_catalog,
                claim_evidence_map=claim_evidence_map,
                table_id=table_id,
            )
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
                "claim_ids": claim_ids,
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
            "table2_phenotype_gap_summary",
            "table2_time_to_event_performance_summary",
            "table3_clinical_interpretation_summary",
            "table3_transition_site_support_summary",
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
            elif requirement_short_id == "table2_phenotype_gap_summary":
                output_md_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_phenotype_gap_summary.md"
                output_csv_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_phenotype_gap_summary.csv"
                default_title = "Phenotype-level clinical characteristics and treatment-gap rates"
                default_caption = (
                    "Phenotype-level clinical characteristics and treatment-gap rates rendered as a compact measure-value table."
                )
            elif requirement_short_id == "table3_clinical_interpretation_summary":
                output_md_path = resolved_paper_root / "tables" / "generated" / f"{table_id}_clinical_interpretation_summary.md"
                default_title = "Clinical interpretation summary"
                default_caption = "Clinical interpretation anchors for prespecified risk groups and use cases."
            elif requirement_short_id == "table3_transition_site_support_summary":
                output_md_path = (
                    resolved_paper_root / "tables" / "generated" / f"{table_id}_transition_site_support_summary.md"
                )
                output_csv_path = (
                    resolved_paper_root / "tables" / "generated" / f"{table_id}_transition_site_support_summary.csv"
                )
                default_title = "Transition stability and site-held-out support summary"
                default_caption = "Transition and held-out-site support rendered as a compact measure-value table."
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
            claim_ids = _claim_ids_for_table(
                table_catalog=table_catalog,
                claim_evidence_map=claim_evidence_map,
                table_id=table_id,
            )
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
                "claim_ids": claim_ids,
                "render_result": render_result,
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
            try:
                payload_path, display_payload = _load_evidence_display_payload(
                    paper_root=resolved_paper_root,
                    spec=spec,
                    display_id=display_id,
                )
            except (FileNotFoundError, ValueError) as exc:
                raise ValueError(
                    "evidence display payload unavailable for "
                    f"display_id=`{display_id}`, registry_requirement_key=`{registry_requirement_key}`, "
                    f"requirement_key=`{requirement_key}`, requirement_short_id=`{requirement_short_id}`, "
                    f"template_id=`{spec.template_id}`, input_schema_id=`{spec.input_schema_id}`; "
                    f"expected_input_path=`{_evidence_payload_path(paper_root=resolved_paper_root, input_schema_id=spec.input_schema_id)}`"
                ) from exc
            payload_template_id = str(display_payload.get("template_id") or "").strip()
            if payload_template_id and payload_template_id != spec.template_id:
                spec = display_registry.get_evidence_figure_spec(payload_template_id)
                pack_id, template_short_id = _require_namespaced_registry_id(
                    spec.template_id,
                    label=f"{requirement_key} template_id",
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
            output_svg_path = (
                resolved_paper_root / "figures" / "generated" / f"{figure_id}_{template_short_id}.svg"
                if "svg" in spec.required_exports
                else None
            )
            layout_sidecar_path = resolved_paper_root / "figures" / "generated" / f"{figure_id}_{template_short_id}.layout.json"
            _prepare_python_render_output_paths(
                output_png_path=output_png_path,
                output_pdf_path=output_pdf_path,
                layout_sidecar_path=layout_sidecar_path,
                output_svg_path=output_svg_path,
            )
            render_result = _render_evidence_figure_by_template_runtime(
                template_id=spec.template_id,
                display_payload=render_payload,
                paper_root=resolved_paper_root,
                figure_id=figure_id,
                output_png_path=output_png_path,
                output_pdf_path=output_pdf_path,
                layout_sidecar_path=layout_sidecar_path,
                output_svg_path=output_svg_path,
            )
            layout_sidecar = _load_layout_sidecar_or_raise(path=layout_sidecar_path, template_id=spec.template_id)
            layout_sidecar["render_context"] = render_context
            dump_json(layout_sidecar_path, layout_sidecar)
            purpose_first_fields = _purpose_first_renderer_fields(layout_sidecar)
            qc_result = display_layout_qc.run_display_layout_qc(
                qc_profile=spec.layout_qc_profile,
                layout_sidecar=layout_sidecar,
            )
            qc_result["layout_sidecar_path"] = _paper_relative_path(layout_sidecar_path, paper_root=resolved_paper_root)
            written_files.extend([str(output_png_path), str(output_pdf_path), str(layout_sidecar_path)])
            if output_svg_path is not None and output_svg_path.exists():
                written_files.append(str(output_svg_path))
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
                    *(
                        [_paper_relative_path(output_svg_path, paper_root=resolved_paper_root)]
                        if output_svg_path is not None and output_svg_path.exists()
                        else []
                    ),
                ],
                "source_paths": [
                    _paper_relative_path(payload_path, paper_root=resolved_paper_root),
                ],
                "claim_ids": [],
                "render_context": render_context,
                "render_result": render_result,
                **purpose_first_fields,
            }
            figure_catalog["figures"] = _replace_catalog_entry(
                list(figure_catalog.get("figures") or []),
                key="figure_id",
                value=figure_id,
                entry=entry,
            )
            figures_materialized.append(figure_id)
            continue

    if (resolved_paper_root / "submission_graphical_abstract.json").exists():
        if style_profile is None:
            style_profile = publication_display_contract.load_publication_style_profile(
                resolved_paper_root / "publication_style_profile.json"
            )
        if display_overrides is None:
            display_overrides = publication_display_contract.load_display_overrides(
                resolved_paper_root / "display_overrides.json"
            )
        figure_id, submission_written_files = _materialize_submission_graphical_abstract(
            paper_root=resolved_paper_root,
            figure_catalog=figure_catalog,
            style_profile=style_profile,
            display_overrides=display_overrides,
        )
        written_files.extend(submission_written_files)
        if figure_id is not None and figure_id not in figures_materialized:
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
    visual_audit_receipt = _write_catalog_visual_audit_receipt(
        paper_root=resolved_paper_root,
        figure_catalog=figure_catalog,
    )
    display_pack_sync_result = display_pack_surface_sync.sync_display_pack_surface(
        paper_root=resolved_paper_root,
    )
    display_pack_lock_path = display_pack_lock.write_display_pack_lock(
        paper_root=resolved_paper_root,
        repo_root=_REPO_ROOT,
    )
    synced_files = [
        str((resolved_paper_root.parent / str(path)).resolve())
        for path in display_pack_sync_result.get("updated_files", [])
    ]
    written_files.extend(
        [
            str(resolved_paper_root / "figures" / "figure_catalog.json"),
            str(resolved_paper_root / "tables" / "table_catalog.json"),
            *([str(resolved_paper_root / "figure_visual_audit_receipt.json")] if visual_audit_receipt else []),
            *synced_files,
            str(display_pack_lock_path),
            *readme_paths,
        ]
    )
    return {
        "status": "materialized",
        "paper_root": str(resolved_paper_root),
        "figures_materialized": figures_materialized,
        "tables_materialized": tables_materialized,
        "source_hydration": source_hydration_result,
        "display_pack_surface_sync": display_pack_sync_result,
        "visual_audit_receipt": (
            {
                "path": str(resolved_paper_root / "figure_visual_audit_receipt.json"),
                "final_status": visual_audit_receipt["final_status"],
                "inspected_artifact_count": len(visual_audit_receipt["inspected_artifacts"]),
            }
            if visual_audit_receipt
            else None
        ),
        "pruned_generated_paths": pruned_generated_paths,
        "written_files": written_files,
    }


__all__ = [
    "_iter_display_surface_entries",
    "materialize_display_visual_audit",
    "materialize_display_surface",
]
