from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_load_medical_figure_spec_binds_intent_template_kind_and_medical_semantics(tmp_path: Path) -> None:
    from med_autoscience.medical_figure_spec_contract import load_medical_figure_spec

    path = tmp_path / "figure_spec.json"
    _write_json(
        path,
        {
            "schema_version": 1,
            "figure_id": "F1",
            "intent_ref": "paper/figure_intent.json#/figures/F1",
            "template_id": "fenggaolab.org.medical-display-core::time_to_event_discrimination_calibration_panel",
            "figure_kind": "evidence_figure",
            "medical_semantics": {
                "cohort_ref": "study/cohorts/derivation",
                "endpoint_ref": "endpoint:mace",
                "model_ref": "model:cox-primary",
                "risk_horizon": "5y",
                "effect_estimate_ref": "analysis/effects/hazard_ratio_primary",
                "claim_role": "primary_evidence",
            },
            "panels": [
                {
                    "panel_id": "A",
                    "data_role": "discrimination",
                    "mark_role": "time_dependent_auc_curve",
                }
            ],
        },
    )

    payload = load_medical_figure_spec(path)

    assert payload["figure_id"] == "F1"
    assert payload["figure_kind"] == "evidence_figure"
    assert payload["medical_semantics"]["cohort_ref"] == "study/cohorts/derivation"
    assert payload["panels"][0]["mark_role"] == "time_dependent_auc_curve"


def test_load_medical_figure_spec_rejects_missing_required_binding_field(tmp_path: Path) -> None:
    from med_autoscience.medical_figure_spec_contract import load_medical_figure_spec

    path = tmp_path / "figure_spec.json"
    _write_json(
        path,
        {
            "schema_version": 1,
            "figure_id": "F1",
            "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
            "figure_kind": "evidence_figure",
            "medical_semantics": {
                "cohort_ref": "study/cohorts/derivation",
                "endpoint_ref": "endpoint:mace",
                "claim_role": "primary_evidence",
            },
        },
    )

    with pytest.raises(ValueError, match="intent_ref"):
        load_medical_figure_spec(path)


def test_load_medical_figure_spec_requires_evidence_cohort_and_endpoint(tmp_path: Path) -> None:
    from med_autoscience.medical_figure_spec_contract import load_medical_figure_spec

    path = tmp_path / "figure_spec.json"
    _write_json(
        path,
        {
            "schema_version": 1,
            "figure_id": "F2",
            "intent_ref": "paper/figure_intent.json#/figures/F2",
            "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
            "figure_kind": "evidence_figure",
            "medical_semantics": {
                "endpoint_ref": "endpoint:mace",
                "claim_role": "primary_evidence",
            },
        },
    )

    with pytest.raises(ValueError, match="cohort_ref"):
        load_medical_figure_spec(path)


def test_load_medical_figure_spec_allows_illustration_shell_without_effect_estimate(tmp_path: Path) -> None:
    from med_autoscience.medical_figure_spec_contract import load_medical_figure_spec

    path = tmp_path / "figure_spec.json"
    _write_json(
        path,
        {
            "schema_version": 1,
            "figure_id": "GA1",
            "intent_ref": "paper/figure_intent.json#/figures/GA1",
            "template_id": "fenggaolab.org.medical-display-core::submission_graphical_abstract",
            "figure_kind": "illustration_shell",
            "medical_semantics": {
                "cohort_ref": "study/cohorts/derivation",
                "endpoint_ref": "endpoint:mace",
                "model_ref": "model:cox-primary",
                "risk_horizon": "5y",
                "claim_role": "contextual_illustration",
            },
        },
    )

    payload = load_medical_figure_spec(path)

    assert payload["figure_kind"] == "illustration_shell"
    assert "effect_estimate_ref" not in payload["medical_semantics"]


def test_load_medical_figure_spec_validates_panel_grammar(tmp_path: Path) -> None:
    from med_autoscience.medical_figure_spec_contract import load_medical_figure_spec

    path = tmp_path / "figure_spec.json"
    _write_json(
        path,
        {
            "schema_version": 1,
            "figure_id": "F3",
            "intent_ref": "paper/figure_intent.json#/figures/F3",
            "template_id": "fenggaolab.org.medical-display-core::calibration_slope_intercept",
            "figure_kind": "evidence_figure",
            "medical_semantics": {
                "cohort_ref": "study/cohorts/validation",
                "endpoint_ref": "endpoint:mace",
                "model_ref": "model:cox-primary",
                "risk_horizon": "5y",
                "claim_role": "supporting_evidence",
            },
            "panels": [{"panel_id": "A", "data_role": "calibration"}],
        },
    )

    with pytest.raises(ValueError, match="mark_role"):
        load_medical_figure_spec(path)


def test_load_medical_figure_specs_accepts_multi_figure_batch(tmp_path: Path) -> None:
    from med_autoscience.medical_figure_spec_contract import load_medical_figure_specs

    path = tmp_path / "figure_specs.json"
    _write_json(
        path,
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "intent_ref": "paper/figure_intent.json#/figures/F1",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
                    "figure_kind": "evidence_figure",
                    "medical_semantics": {
                        "cohort_ref": "study/cohorts/derivation",
                        "endpoint_ref": "endpoint:mace",
                        "claim_role": "primary_evidence",
                    },
                },
                {
                    "schema_version": 1,
                    "figure_id": "F2",
                    "intent_ref": "paper/figure_intent.json#/figures/F2",
                    "template_id": "fenggaolab.org.medical-display-core::time_dependent_roc_horizon",
                    "figure_kind": "evidence_figure",
                    "medical_semantics": {
                        "cohort_ref": "study/cohorts/validation",
                        "endpoint_ref": "endpoint:mace",
                        "risk_horizon": "5y",
                        "claim_role": "secondary_evidence",
                    },
                },
            ],
        },
    )

    payload = load_medical_figure_specs(path)

    assert [item["figure_id"] for item in payload["figures"]] == ["F1", "F2"]
    assert payload["figures"][0]["schema_version"] == 1


def test_load_medical_figure_specs_rejects_duplicate_figure_id(tmp_path: Path) -> None:
    from med_autoscience.medical_figure_spec_contract import load_medical_figure_specs

    path = tmp_path / "figure_specs.json"
    _write_json(
        path,
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "intent_ref": "paper/figure_intent.json#/figures/F1",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
                    "figure_kind": "evidence_figure",
                    "medical_semantics": {
                        "cohort_ref": "study/cohorts/derivation",
                        "endpoint_ref": "endpoint:mace",
                        "claim_role": "primary_evidence",
                    },
                },
                {
                    "figure_id": "F1",
                    "intent_ref": "paper/figure_intent.json#/figures/F1b",
                    "template_id": "fenggaolab.org.medical-display-core::roc_curve_binary",
                    "figure_kind": "evidence_figure",
                    "medical_semantics": {
                        "cohort_ref": "study/cohorts/validation",
                        "endpoint_ref": "endpoint:mace",
                        "claim_role": "secondary_evidence",
                    },
                },
            ],
        },
    )

    with pytest.raises(ValueError, match="duplicate"):
        load_medical_figure_specs(path)


def test_root_contract_indexes_medical_figure_spec_surface() -> None:
    from med_autoscience.medical_figure_spec_contract import (
        MEDICAL_FIGURE_SPEC_BASENAME,
        MEDICAL_FIGURE_SPECS_BASENAME,
    )

    contract = json.loads((REPO_ROOT / "contracts" / "medical_figure_spec_contract.json").read_text())

    assert contract["contract_id"] == "medical_figure_spec_contract.v1"
    assert contract["source_module"] == "src/med_autoscience/medical_figure_spec_contract.py"
    assert contract["paper_surface"]["path"] == f"paper/{MEDICAL_FIGURE_SPEC_BASENAME}"
    assert contract["batch_paper_surface"]["path"] == f"paper/{MEDICAL_FIGURE_SPECS_BASENAME}"
    assert contract["paper_surface"]["loader"] == "med_autoscience.medical_figure_spec_contract:load_medical_figure_spec"
    assert contract["paper_surface"]["authority_boundary"] == (
        "Declarative medical figure grammar only; it binds figure intent, Display Template, "
        "and medical semantics without rendering figures, changing data/statistics, or issuing "
        "publication readiness verdicts."
    )
