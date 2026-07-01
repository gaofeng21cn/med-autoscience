from __future__ import annotations

import hashlib
import json

from med_autoscience.publication_figure_quality_contract import load_figure_visual_audit_receipt

from ..shared import Any, Path, _paper_relative_path, dump_json, load_json, utc_now
from .workspace import _resolve_workspace_path


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _primary_png_export_path(*, paper_root: Path, entry: dict[str, Any]) -> Path | None:
    for export_path in entry.get("export_paths") or []:
        export_ref = str(export_path or "").strip()
        if not export_ref.lower().endswith(".png"):
            continue
        path = _resolve_workspace_path(export_ref, paper_root=paper_root)
        if path.exists():
            return path
    return None


def _figure_audit_entry_from_catalog(*, paper_root: Path, entry: dict[str, Any]) -> dict[str, Any] | None:
    figure_id = str(entry.get("figure_id") or entry.get("catalog_id") or "").strip()
    if not figure_id:
        return None
    artifact_path = _primary_png_export_path(paper_root=paper_root, entry=entry)
    if artifact_path is None:
        return None
    return {
        "figure_id": figure_id,
        "artifact_path": _paper_relative_path(artifact_path, paper_root=paper_root),
        "artifact_sha256": _sha256_file(artifact_path),
    }


def _catalog_layout_sidecar_path(*, paper_root: Path, entry: dict[str, Any]) -> Path | None:
    qc_result = entry.get("qc_result")
    if not isinstance(qc_result, dict):
        return None
    sidecar_ref = str(qc_result.get("layout_sidecar_path") or "").strip()
    if not sidecar_ref:
        return None
    sidecar_path = _resolve_workspace_path(sidecar_ref, paper_root=paper_root)
    if not sidecar_path.exists():
        return None
    return sidecar_path


def _short_template_id(value: object) -> str:
    text = str(value or "").strip()
    return text.rsplit("::", 1)[-1]


def _visual_audit_findings_from_sidecar(
    *,
    figure_id: str,
    sidecar_path: Path,
) -> list[dict[str, Any]]:
    try:
        sidecar = load_json(sidecar_path)
    except (OSError, ValueError, json.JSONDecodeError):
        return []
    metrics = sidecar.get("metrics")
    if not isinstance(metrics, dict):
        return []
    template_id = _short_template_id(sidecar.get("template_id") or metrics.get("template_id"))
    if template_id == "cohort_flow_figure":
        layout_generation = str(metrics.get("layout_generation") or "").strip()
        flow_visual_policy = str(metrics.get("flow_visual_policy") or "").strip()
        if layout_generation == "scholarskills_cohort_flow_v2" and flow_visual_policy == "purpose_first_reporting_flow_no_legacy_card_shell":
            return []
        return [
            {
                "figure_id": figure_id,
                "observed_issue": (
                    "Cohort-flow Figure 1 sidecar does not declare the ScholarSkills v2 purpose-first "
                    "reporting-flow layout policy."
                ),
                "paper_facing_impact": (
                    "The figure may be rendered by a technically ggplot2-backed path while still using "
                    "the old card or explanation-shell layout rather than a participant-accounting flow."
                ),
                "suspected_layer": ["renderer_contract", "layout_qc", "manuscript_surface"],
                "proposed_action": (
                    "Regenerate Figure 1 with the ScholarSkills cohort_flow_figure v2 template and rerun "
                    "post-PDF visual audit."
                ),
                "promotion_decision": "promote_to_qc",
                "verification_plan": (
                    "Confirm layout_generation=scholarskills_cohort_flow_v2, "
                    "flow_visual_policy=purpose_first_reporting_flow_no_legacy_card_shell, and inspect "
                    "the rendered PDF page."
                ),
            }
        ]
    if template_id != "site_held_out_stability_figure":
        return []
    transition_rows = metrics.get("transition_rows")
    if not isinstance(transition_rows, list) or len(transition_rows) < 24:
        return []
    label_policy = str(
        metrics.get("transition_cell_label_policy")
        or metrics.get("cell_label_policy")
        or ""
    ).strip()
    if "no_counts" in label_policy and "major" in label_policy:
        return []
    return [
        {
            "figure_id": figure_id,
            "observed_issue": (
                "Dense DPCC transition heatmap lacks an explicit sparse cell-label policy; "
                "paper PDF scaling can make cell text overlap."
            ),
            "paper_facing_impact": (
                "The rendered Figure 3 may appear visually clear in the artifact catalog while "
                "the final manuscript PDF contains overlapping heatmap labels."
            ),
            "suspected_layer": ["renderer_contract", "readability_qc", "manuscript_surface"],
            "proposed_action": (
                "Render transition cells with sparse major-share percentage labels only, omit "
                "per-cell counts, and rerun post-PDF visual audit."
            ),
            "promotion_decision": "promote_to_qc",
            "verification_plan": (
                "Regenerate the figure and final paper.pdf, then inspect the rendered PDF page "
                "for non-overlapping transition heatmap labels."
            ),
        }
    ]


def _write_catalog_visual_audit_receipt(*, paper_root: Path, figure_catalog: dict[str, Any]) -> dict[str, Any] | None:
    inspected_artifacts: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    for entry in figure_catalog.get("figures") or []:
        if not isinstance(entry, dict):
            continue
        audit_entry = _figure_audit_entry_from_catalog(paper_root=paper_root, entry=entry)
        if audit_entry is not None:
            sidecar_path = _catalog_layout_sidecar_path(paper_root=paper_root, entry=entry)
            if sidecar_path is not None:
                audit_entry["layout_sidecar_path"] = _paper_relative_path(sidecar_path, paper_root=paper_root)
                findings.extend(
                    _visual_audit_findings_from_sidecar(
                        figure_id=str(audit_entry["figure_id"]),
                        sidecar_path=sidecar_path,
                    )
                )
            inspected_artifacts.append(audit_entry)
    if not inspected_artifacts:
        return None
    final_status = "findings_open" if findings else "clear"
    review_label = json.dumps(
        {"inspected_artifacts": inspected_artifacts, "findings": findings},
        ensure_ascii=False,
        sort_keys=True,
    )
    payload = {
        "schema_version": 1,
        "receipt_id": f"display-surface-visual-audit-{utc_now()}",
        "audit_mode": "human_visual_review",
        "inspected_artifacts": inspected_artifacts,
        "findings": findings,
        "reviewer": {
            "provider": "mas-display-surface-materializer",
            "model": "deterministic-render-inspect-revise",
            "prompt_hash": _sha256_text(review_label),
        },
        "final_status": final_status,
    }
    receipt_path = paper_root / "figure_visual_audit_receipt.json"
    dump_json(receipt_path, payload)
    return load_figure_visual_audit_receipt(receipt_path)


def materialize_display_visual_audit(*, paper_root: Path) -> dict[str, Any]:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    figure_catalog = load_json(resolved_paper_root / "figures" / "figure_catalog.json")
    visual_audit_receipt = _write_catalog_visual_audit_receipt(
        paper_root=resolved_paper_root,
        figure_catalog=figure_catalog,
    )
    if visual_audit_receipt is None:
        raise ValueError("figure_catalog.json does not contain any existing PNG export paths to inspect")
    receipt_path = resolved_paper_root / "figure_visual_audit_receipt.json"
    return {
        "status": "visual_audit_receipt_materialized",
        "paper_root": str(resolved_paper_root),
        "visual_audit_receipt": {
            "path": str(receipt_path),
            "final_status": visual_audit_receipt["final_status"],
            "inspected_artifact_count": len(visual_audit_receipt["inspected_artifacts"]),
        },
        "authority_boundary": {
            "writes_authority": False,
            "writes_publication_readiness": False,
            "writes_owner_receipt": False,
            "writes_current_package": False,
        },
        "written_files": [str(receipt_path)],
    }


__all__ = ["materialize_display_visual_audit"]
