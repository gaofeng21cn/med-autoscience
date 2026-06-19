from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_load_figure_intent_requires_claim_data_template_and_kind(tmp_path: Path) -> None:
    from med_autoscience.publication_figure_quality_contract import load_figure_intent

    path = tmp_path / "figure_intent.json"
    _write_json(
        path,
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "claim_ref": "claim:primary-discrimination",
                    "data_ref": "paper/data/frozen/primary_curves.json",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
                    "figure_kind": "evidence_figure",
                }
            ],
        },
    )

    payload = load_figure_intent(path)

    assert payload["figures"][0]["figure_id"] == "F1"
    assert payload["figures"][0]["figure_kind"] == "evidence_figure"


def test_load_figure_intent_rejects_missing_binding_fields(tmp_path: Path) -> None:
    from med_autoscience.publication_figure_quality_contract import load_figure_intent

    path = tmp_path / "figure_intent.json"
    _write_json(
        path,
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
                    "figure_kind": "evidence_figure",
                }
            ],
        },
    )

    with pytest.raises(ValueError, match="claim_ref"):
        load_figure_intent(path)


def test_load_style_reference_bundle_classifies_like_reject_and_adopt_refs(tmp_path: Path) -> None:
    from med_autoscience.publication_figure_quality_contract import load_figure_style_reference_bundle

    path = tmp_path / "figure_style_reference_bundle.json"
    _write_json(
        path,
        {
            "schema_version": 1,
            "bundle_id": "lab-clinical-display-style-v1",
            "references": [
                {
                    "reference_id": "nature-fig2",
                    "source_ref": "https://example.org/paper",
                    "decision": "adopt",
                    "applies_to": ["fenggaolab.org.medical-display-core::roc_curve_binary"],
                    "style_notes": ["compact legend", "gray-print safe palette"],
                },
                {
                    "reference_id": "busy-abstract",
                    "source_ref": "https://example.org/abstract",
                    "decision": "reject",
                    "applies_to": ["illustration_shell"],
                    "style_notes": ["too much decorative density"],
                },
            ],
        },
    )

    payload = load_figure_style_reference_bundle(path)

    assert payload["references"][0]["decision"] == "adopt"
    assert payload["references"][1]["decision"] == "reject"


def test_load_visual_audit_receipt_requires_rendered_artifact_findings_and_vlm_boundary(tmp_path: Path) -> None:
    from med_autoscience.publication_figure_quality_contract import load_figure_visual_audit_receipt

    path = tmp_path / "figure_visual_audit_receipt.json"
    _write_json(
        path,
        {
            "schema_version": 1,
            "receipt_id": "visual-audit-20260610",
            "audit_mode": "vlm_visual_verification",
            "inspected_artifacts": [
                {
                    "figure_id": "F1",
                    "artifact_path": "paper/figures/generated/F1.png",
                    "artifact_sha256": "a" * 64,
                }
            ],
            "findings": [
                {
                    "figure_id": "F1",
                    "observed_issue": "Legend overlaps the lower confidence band.",
                    "paper_facing_impact": "The reader cannot distinguish model and comparator curves.",
                    "suspected_layer": ["display_override"],
                    "proposed_action": "Move legend outside the plotting area.",
                    "promotion_decision": "promote_to_qc",
                    "verification_plan": "Rerender and rerun layout QC plus visual audit.",
                }
            ],
            "reviewer": {
                "provider": "openai",
                "model": "gpt-5-vlm",
                "prompt_hash": "b" * 64,
            },
            "final_status": "findings_open",
        },
    )

    payload = load_figure_visual_audit_receipt(path)

    assert payload["audit_mode"] == "vlm_visual_verification"
    assert payload["findings"][0]["promotion_decision"] == "promote_to_qc"


def test_load_ai_illustration_receipt_forbids_scientific_claims(tmp_path: Path) -> None:
    from med_autoscience.publication_figure_quality_contract import load_ai_illustration_receipt

    path = tmp_path / "ai_illustration_receipt.json"
    _write_json(
        path,
        {
            "schema_version": 1,
            "receipt_id": "illustration-candidate-20260610",
            "illustrations": [
                {
                    "figure_id": "GA1",
                    "template_id": "fenggaolab.org.medical-display-core::submission_graphical_abstract",
                    "prompt_hash": "c" * 64,
                    "provider": "openai",
                    "model": "gpt-image-1",
                    "review_log_ref": "paper/figures/generated/GA1.review.json",
                    "acceptance": "human_accepted",
                    "final_export_path": "paper/figures/generated/GA1.svg",
                    "scientific_claim_carried": False,
                }
            ],
        },
    )

    payload = load_ai_illustration_receipt(path)

    assert payload["illustrations"][0]["acceptance"] == "human_accepted"


def test_load_ai_illustration_receipt_rejects_claim_bearing_candidates(tmp_path: Path) -> None:
    from med_autoscience.publication_figure_quality_contract import load_ai_illustration_receipt

    path = tmp_path / "ai_illustration_receipt.json"
    _write_json(
        path,
        {
            "schema_version": 1,
            "receipt_id": "bad-illustration",
            "illustrations": [
                {
                    "figure_id": "GA1",
                    "template_id": "fenggaolab.org.medical-display-core::submission_graphical_abstract",
                    "prompt_hash": "c" * 64,
                    "provider": "openai",
                    "model": "gpt-image-1",
                    "review_log_ref": "paper/figures/generated/GA1.review.json",
                    "acceptance": "ai_recommended",
                    "final_export_path": "paper/figures/generated/GA1.svg",
                    "scientific_claim_carried": True,
                }
            ],
        },
    )

    with pytest.raises(ValueError, match="scientific_claim_carried"):
        load_ai_illustration_receipt(path)


def test_load_figure_render_receipt_requires_backend_export_and_source_boundaries(tmp_path: Path) -> None:
    from med_autoscience.publication_figure_quality_contract import load_figure_render_receipt

    path = tmp_path / "figure_render_receipt.json"
    _write_json(
        path,
        {
            "schema_version": 1,
            "receipt_id": "render-receipt-20260618",
            "source_project": "nature-skills",
            "source_commit": "1cb9070fdd94929d5f267ce6585ac87e2cba60b3",
            "figures": [
                {
                    "figure_id": "F1",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
                    "selected_backend": "python",
                    "execution_mode": "python_plugin",
                    "backend_exclusivity_proof": {
                        "selected_backend": "python",
                        "observed_renderer_family": "python",
                        "cross_backend_visual_fallback_used": False,
                        "non_selected_backend_rendered_artifacts": [],
                    },
                    "export_formats": ["png", "pdf"],
                    "editable_text_required": True,
                    "editable_text_check_ref": "paper/figures/generated/F1.pdf",
                    "source_data_refs": ["paper/data/frozen/primary_curve.json"],
                    "source_data_digests": {"paper/data/frozen/primary_curve.json": "data-digest-primary"},
                    "statistics_refs": ["analysis/statistics/auc_primary"],
                    "rendered_artifact_refs": ["paper/figures/generated/F1.png", "paper/figures/generated/F1.pdf"],
                    "visual_qa_ref": "paper/figure_visual_audit_receipt.json",
                    "authority_boundary": {
                        "can_authorize_publication_readiness": False,
                        "can_authorize_quality_verdict": False,
                        "can_mutate_data_or_statistics": False,
                    },
                }
            ],
            "authority_boundary": {
                "can_authorize_publication_readiness": False,
                "can_authorize_quality_verdict": False,
                "can_mutate_data_or_statistics": False,
            },
        },
    )

    payload = load_figure_render_receipt(path)

    figure = payload["figures"][0]
    assert figure["selected_backend"] == "python"
    assert figure["backend_exclusivity_proof"]["cross_backend_visual_fallback_used"] is False
    assert figure["export_formats"] == ["png", "pdf"]
    assert figure["authority_boundary"]["can_authorize_publication_readiness"] is False


def test_load_figure_render_receipt_rejects_cross_backend_fallback(tmp_path: Path) -> None:
    from med_autoscience.publication_figure_quality_contract import load_figure_render_receipt

    path = tmp_path / "figure_render_receipt.json"
    _write_json(
        path,
        {
            "schema_version": 1,
            "receipt_id": "bad-render-receipt",
            "figures": [
                {
                    "figure_id": "F1",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
                    "selected_backend": "python",
                    "execution_mode": "python_plugin",
                    "backend_exclusivity_proof": {
                        "selected_backend": "python",
                        "observed_renderer_family": "r_ggplot2",
                        "cross_backend_visual_fallback_used": True,
                        "non_selected_backend_rendered_artifacts": ["paper/figures/generated/F1.preview.png"],
                    },
                    "export_formats": ["png", "pdf"],
                    "editable_text_required": True,
                    "editable_text_check_ref": "paper/figures/generated/F1.pdf",
                    "source_data_refs": ["paper/data/frozen/primary_curve.json"],
                    "source_data_digests": {"paper/data/frozen/primary_curve.json": "data-digest-primary"},
                    "statistics_refs": ["analysis/statistics/auc_primary"],
                    "rendered_artifact_refs": ["paper/figures/generated/F1.png", "paper/figures/generated/F1.pdf"],
                    "visual_qa_ref": "paper/figure_visual_audit_receipt.json",
                    "authority_boundary": {
                        "can_authorize_publication_readiness": False,
                        "can_authorize_quality_verdict": False,
                        "can_mutate_data_or_statistics": False,
                    },
                }
            ],
            "authority_boundary": {
                "can_authorize_publication_readiness": False,
                "can_authorize_quality_verdict": False,
                "can_mutate_data_or_statistics": False,
            },
        },
    )

    with pytest.raises(ValueError, match="cross_backend_visual_fallback_used"):
        load_figure_render_receipt(path)


def test_collect_publication_figure_quality_refs_reports_present_and_missing_surfaces(tmp_path: Path) -> None:
    from med_autoscience.publication_figure_quality_contract import collect_publication_figure_quality_refs

    paper_root = tmp_path / "paper"
    _write_json(
        paper_root / "figure_intent.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "claim_ref": "claim:primary",
                    "data_ref": "paper/data/frozen/primary.json",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
                    "figure_kind": "evidence_figure",
                }
            ],
        },
    )

    refs = collect_publication_figure_quality_refs(paper_root=paper_root)

    assert refs["figure_intent"]["path"] == "paper/figure_intent.json"
    assert refs["figure_intent"]["status"] == "present"
    assert refs["figure_render_receipt"]["status"] == "missing"
    assert refs["figure_style_reference_bundle"]["status"] == "missing"


def test_root_contract_indexes_publication_figure_quality_surfaces() -> None:
    from med_autoscience.publication_figure_quality_contract import (
        AI_ILLUSTRATION_RECEIPT_BASENAME,
        FIGURE_RENDER_RECEIPT_BASENAME,
        FIGURE_POLISH_LIFECYCLE_BASENAME,
        FIGURE_INTENT_BASENAME,
        FIGURE_STYLE_REFERENCE_BUNDLE_BASENAME,
        FIGURE_VISUAL_AUDIT_RECEIPT_BASENAME,
        MEDICAL_FIGURE_SPEC_BASENAME,
        MEDICAL_FIGURE_SPECS_BASENAME,
    )

    contract = json.loads((REPO_ROOT / "contracts" / "publication_figure_quality_contract.json").read_text())

    assert contract["source_module"] == "src/med_autoscience/publication_figure_quality_contract.py"
    assert contract["paper_surfaces"]["figure_intent"]["path"] == f"paper/{FIGURE_INTENT_BASENAME}"
    assert contract["paper_surfaces"]["medical_figure_spec"]["path"] == f"paper/{MEDICAL_FIGURE_SPEC_BASENAME}"
    assert contract["paper_surfaces"]["medical_figure_specs"]["path"] == f"paper/{MEDICAL_FIGURE_SPECS_BASENAME}"
    assert (
        contract["paper_surfaces"]["figure_style_reference_bundle"]["path"]
        == f"paper/{FIGURE_STYLE_REFERENCE_BUNDLE_BASENAME}"
    )
    assert (
        contract["paper_surfaces"]["figure_visual_audit_receipt"]["path"]
        == f"paper/{FIGURE_VISUAL_AUDIT_RECEIPT_BASENAME}"
    )
    assert contract["paper_surfaces"]["figure_render_receipt"]["path"] == f"paper/{FIGURE_RENDER_RECEIPT_BASENAME}"
    assert (
        contract["paper_surfaces"]["figure_polish_lifecycle"]["path"]
        == f"paper/{FIGURE_POLISH_LIFECYCLE_BASENAME}"
    )
    assert contract["paper_surfaces"]["ai_illustration_receipt"]["path"] == f"paper/{AI_ILLUSTRATION_RECEIPT_BASENAME}"
    assert contract["consumers"]["display_pack_lock"]["field"] == "publication_figure_quality_refs"
