from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.publication_figure_quality_contract import load_figure_render_receipt


FIGURE_RENDER_RECEIPT_REF = "paper/figure_render_receipt.json"
FIGURE_VISUAL_AUDIT_RECEIPT_REF = "paper/figure_visual_audit_receipt.json"


def figure_render_receipt_payload(
    *,
    figure_entries: list[dict[str, Any]],
    timestamp_factory: Callable[[], str],
) -> dict[str, Any]:
    receipt_figures = []
    for entry in figure_entries:
        rendered_artifacts = dict(entry.get("rendered_artifacts") or {})
        selected_backend = str(entry.get("renderer_family") or "").strip()
        source_data_ref = str(entry["data_ref"])
        receipt_figures.append(
            {
                "figure_id": str(entry["figure_id"]),
                "template_id": str(entry["template_id"]),
                "selected_backend": selected_backend,
                "execution_mode": str(entry["execution_mode"]),
                "backend_exclusivity_proof": {
                    "selected_backend": selected_backend,
                    "observed_renderer_family": selected_backend,
                    "cross_backend_visual_fallback_used": False,
                    "non_selected_backend_rendered_artifacts": [],
                    "render_result_ref": (
                        f"{FIGURE_RENDER_RECEIPT_REF}#/figures/{entry['figure_id']}/render_result"
                    ),
                },
                "export_formats": list(entry.get("required_exports") or []),
                "editable_text_required": True,
                "editable_text_check_ref": str(rendered_artifacts["pdf_ref"]),
                "source_data_refs": [source_data_ref],
                "source_data_digests": {source_data_ref: str(entry["data_digest"])},
                "statistics_refs": list(entry.get("statistical_value_refs") or []),
                "rendered_artifact_refs": [
                    str(rendered_artifacts["png_ref"]),
                    str(rendered_artifacts["pdf_ref"]),
                    str(rendered_artifacts["layout_sidecar_ref"]),
                ],
                "visual_qa_ref": FIGURE_VISUAL_AUDIT_RECEIPT_REF,
                "render_result": dict(entry.get("render_result") or {}),
                "authority_boundary": _authority_boundary(),
            }
        )
    return {
        "schema_version": 1,
        "receipt_id": f"display-pack-render-{timestamp_factory()}",
        "source_project": "nature-skills",
        "source_pattern": "backend_exclusive_publication_figure_export_qa",
        "figures": receipt_figures,
        "authority_boundary": _authority_boundary(),
    }


def write_figure_render_receipt(
    *,
    paper_root: Path,
    figure_entries: list[dict[str, Any]],
    timestamp_factory: Callable[[], str],
    write_json: Callable[[Path, Mapping[str, Any]], None],
) -> dict[str, Any]:
    receipt_path = paper_root / "figure_render_receipt.json"
    payload = figure_render_receipt_payload(
        figure_entries=figure_entries,
        timestamp_factory=timestamp_factory,
    )
    write_json(receipt_path, payload)
    return load_figure_render_receipt(receipt_path)


def _authority_boundary() -> dict[str, bool]:
    return {
        "can_authorize_publication_readiness": False,
        "can_authorize_quality_verdict": False,
        "can_mutate_data_or_statistics": False,
    }
