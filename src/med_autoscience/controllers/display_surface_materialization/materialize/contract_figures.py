from __future__ import annotations

import subprocess
import sys

from ..contract_backed_registry import (
    resolve_contract_backed_figure_registry_fields,
    resolve_contract_backed_layout_sidecar_path,
)
from ..renderers import _load_layout_sidecar_or_raise
from ..shared import Any, Path, _paper_relative_path, _replace_catalog_entry, _resolve_figure_catalog_id
from ..shared import display_layout_qc, load_json
from .workspace import _as_string_list, _resolve_workspace_path


def _materialize_contract_backed_figure(
    *,
    paper_root: Path,
    item: dict[str, Any],
    shell_payload: dict[str, Any],
    contract_path: Path,
    figure_catalog: dict[str, Any],
) -> tuple[str, list[str]]:
    source_contract_path = _paper_relative_path(contract_path, paper_root=paper_root)
    if not contract_path.exists():
        raise ValueError(f"contract-backed figure source_contract_path does not exist: {source_contract_path}")
    contract_payload = load_json(contract_path)
    renderer_script_path = str(contract_payload.get("renderer_script_path") or "").strip()
    if not renderer_script_path:
        raise ValueError(f"contract-backed figure `{source_contract_path}` requires renderer_script_path")
    resolved_renderer_script_path = _resolve_workspace_path(renderer_script_path, paper_root=paper_root)
    if not resolved_renderer_script_path.exists():
        raise ValueError(f"contract-backed figure renderer_script_path does not exist: {renderer_script_path}")

    subprocess.run(
        [
            sys.executable,
            str(resolved_renderer_script_path),
            "--output-root",
            str(paper_root),
            "--contract-path",
            str(contract_path),
        ],
        cwd=str(paper_root.parent),
        check=True,
    )

    contract_payload = load_json(contract_path)
    export_paths = _as_string_list(contract_payload.get("rendered_export_paths")) or _as_string_list(
        contract_payload.get("planned_export_paths")
    )
    if not export_paths:
        raise ValueError(f"contract-backed figure `{source_contract_path}` declares no export paths")
    missing_exports = [
        export_path
        for export_path in export_paths
        if not _resolve_workspace_path(export_path, paper_root=paper_root).exists()
    ]
    if missing_exports:
        joined_missing = ", ".join(missing_exports)
        raise ValueError(f"contract-backed figure `{source_contract_path}` did not render expected exports: {joined_missing}")

    display_id = str(contract_payload.get("display_id") or shell_payload.get("display_id") or item.get("display_id") or "").strip()
    figure_id = _resolve_figure_catalog_id(
        display_id=display_id,
        catalog_id=str(
            contract_payload.get("figure_id")
            or shell_payload.get("catalog_id")
            or item.get("catalog_id")
            or ""
        ).strip(),
    )
    registry_fields = resolve_contract_backed_figure_registry_fields(
        paper_root=paper_root,
        item=item,
        shell_payload=shell_payload,
        contract_payload=contract_payload,
        display_id=display_id,
        figure_id=figure_id,
    )
    paper_role = str(contract_payload.get("paper_role") or shell_payload.get("paper_role") or "main_text").strip()
    if paper_role not in registry_fields["allowed_paper_roles"]:
        allowed_roles = ", ".join(registry_fields["allowed_paper_roles"])
        raise ValueError(
            f"contract-backed figure `{figure_id}` paper_role `{paper_role}` is not allowed for "
            f"`{registry_fields['template_id']}`; allowed: {allowed_roles}"
        )
    layout_sidecar_path = resolve_contract_backed_layout_sidecar_path(
        workspace_path_resolver=lambda value: _resolve_workspace_path(value, paper_root=paper_root),
        contract_payload=contract_payload,
        export_paths=export_paths,
    )
    if layout_sidecar_path is None:
        raise ValueError(f"contract-backed figure `{figure_id}` did not produce a layout sidecar")
    layout_sidecar = _load_layout_sidecar_or_raise(path=layout_sidecar_path, template_id=registry_fields["template_id"])
    try:
        qc_result = display_layout_qc.run_display_layout_qc(
            qc_profile=registry_fields["qc_profile"],
            layout_sidecar=layout_sidecar,
        )
    except ValueError as exc:
        raise ValueError(
            f"contract-backed figure `{figure_id}` layout QC failed for "
            f"`{registry_fields['qc_profile']}`: {exc}"
        ) from exc
    qc_result["layout_sidecar_path"] = _paper_relative_path(layout_sidecar_path, paper_root=paper_root)
    if qc_result["status"] != "pass":
        failure_reason = str(qc_result.get("failure_reason") or "").strip()
        issues = qc_result.get("issues")
        if not failure_reason and isinstance(issues, list) and issues:
            first_issue = issues[0]
            if isinstance(first_issue, dict):
                failure_reason = str(first_issue.get("rule_id") or first_issue.get("message") or "").strip()
        if not failure_reason:
            failure_reason = "unknown"
        raise ValueError(
            f"contract-backed figure `{figure_id}` layout QC failed for "
            f"`{registry_fields['qc_profile']}`: {failure_reason}"
        )
    source_paths = _as_string_list(contract_payload.get("source_paths"))
    if not source_paths:
        source_paths = [_paper_relative_path(contract_path, paper_root=paper_root)]
    entry = {
        "figure_id": figure_id,
        "template_id": registry_fields["template_id"],
        "pack_id": registry_fields["pack_id"],
        "renderer_family": registry_fields["renderer_family"],
        "paper_role": paper_role,
        "input_schema_id": registry_fields["input_schema_id"],
        "qc_profile": registry_fields["qc_profile"],
        "qc_result": qc_result,
        "title": str(
            contract_payload.get("title")
            or shell_payload.get("title")
            or contract_payload.get("direct_message")
            or display_id
        ).strip(),
        "caption": str(
            contract_payload.get("caption")
            or shell_payload.get("caption")
            or contract_payload.get("clinical_implication")
            or contract_payload.get("direct_message")
            or ""
        ).strip(),
        "export_paths": export_paths,
        "source_paths": source_paths,
        "claim_ids": _as_string_list(contract_payload.get("claim_ids")),
        "source_contract_path": _paper_relative_path(contract_path, paper_root=paper_root),
        "renderer_script_path": _paper_relative_path(resolved_renderer_script_path, paper_root=paper_root),
    }
    figure_catalog["figures"] = _replace_catalog_entry(
        list(figure_catalog.get("figures") or []),
        key="figure_id",
        value=figure_id,
        entry=entry,
    )
    written_files = [str(_resolve_workspace_path(export_path, paper_root=paper_root)) for export_path in export_paths]
    if layout_sidecar_path is not None:
        written_files.append(str(layout_sidecar_path))
    return figure_id, written_files


__all__ = ["_materialize_contract_backed_figure"]

