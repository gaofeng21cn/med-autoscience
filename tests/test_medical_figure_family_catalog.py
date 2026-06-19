from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from med_autoscience.medical_figure_family_catalog import (
    DEFAULT_CATALOG_ROOT,
    load_medical_figure_family_catalog,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
CATALOG_ROOT = REPO_ROOT / "contracts" / "medical-figure-family-catalog"


def test_medical_figure_family_catalog_loads_full_ontology() -> None:
    catalog = load_medical_figure_family_catalog()

    assert catalog.schema_version == 1
    assert catalog.catalog_id == "medical_figure_family_catalog.v1"
    assert catalog.owner == "MedAutoScience"
    assert catalog.family_count >= 60
    assert [category.category_id for category in catalog.categories] == [
        "study_design_and_flow",
        "population_and_baseline",
        "effect_estimation",
        "survival_and_time_to_event",
        "diagnosis_and_prediction",
        "trial_response_and_safety",
        "meta_analysis",
        "omics_and_molecular",
        "single_cell_and_spatial",
        "ml_explainability_and_causal",
        "longitudinal_and_patient_trajectory",
        "publication_shells",
    ]


def test_ai_policy_keeps_templates_as_loose_quality_floor() -> None:
    policy = load_medical_figure_family_catalog().ai_adaptation_policy

    assert policy["starter_templates_are_floor_not_ceiling"] is True
    assert policy["loose_matching_default"] is True
    assert {"figure_family", "layout", "panel_structure", "palette", "rendering_backend"} <= set(
        policy["ai_may_change"]
    )
    assert {
        "scientific_claim_semantics",
        "statistical_estimand",
        "source_data_and_statistics_refs",
        "auditability",
    } <= set(policy["ai_must_preserve"])


def test_representative_medical_figure_families_are_present() -> None:
    catalog = load_medical_figure_family_catalog()

    discrimination = catalog.family("discrimination_curve")
    assert discrimination.category_id == "diagnosis_and_prediction"
    assert {"roc", "pr", "time_dependent_roc"} <= set(discrimination.canonical_variants)
    assert {"roc_curve_binary", "pr_curve_binary", "time_dependent_roc_horizon"} <= set(
        discrimination.template_seed_ids
    )

    expected_categories = {
        "kaplan_meier_with_risk_table": "survival_and_time_to_event",
        "annotated_heatmap": "omics_and_molecular",
        "shap_summary": "ml_explainability_and_causal",
        "consort_trial_flow": "study_design_and_flow",
        "prisma_review_flow": "study_design_and_flow",
        "multipanel_storyboard": "publication_shells",
    }
    for family_id, category_id in expected_categories.items():
        assert catalog.family(family_id).category_id == category_id


def test_loose_matching_returns_broad_family_instead_of_duplicate_templates() -> None:
    catalog = load_medical_figure_family_catalog()

    assert "discrimination_curve" in {
        family.family_id for family in catalog.families_matching("time dependent ROC and calibration")
    }
    assert "kaplan_meier_with_risk_table" in {
        family.family_id for family in catalog.families_matching("KM plot with number at risk")
    }
    assert "shap_summary" in {family.family_id for family in catalog.families_matching("SHAP beeswarm")}
    assert catalog.families_matching("   ") == ()


def test_catalog_validates_references_across_style_palette_gate_and_sources() -> None:
    catalog = load_medical_figure_family_catalog()

    assert {profile.profile_id for profile in catalog.style_profiles} >= {
        "medpub_neutral",
        "nature_portfolio",
        "clinical_journal",
        "supplement_dense",
    }
    assert {token.token_id for token in catalog.palette_tokens} >= {
        "categorical_accessible",
        "sequential_perceptual",
        "diverging_centered",
        "clinical_status",
    }
    assert {gate.gate_id for gate in catalog.qa_gates} >= {
        "statistical_semantics_preserved",
        "layout_readability",
        "color_accessibility",
        "journal_export",
        "source_data_traceability",
        "ai_redesign_trace",
    }
    assert {source.source_id for source in catalog.external_sources} >= {
        "nature_figure_specs",
        "plos_figure_guidelines",
        "prisma_2020_flow",
        "stard_reporting",
        "patchwork",
        "complexheatmap",
        "viridis",
        "okabe_ito",
    }


def test_catalog_rejects_unknown_family_references(tmp_path: Path) -> None:
    catalog_root = tmp_path / "medical-figure-family-catalog"
    shutil.copytree(DEFAULT_CATALOG_ROOT, catalog_root)
    diagnosis_path = catalog_root / "categories" / "diagnosis_and_prediction.json"
    payload = json.loads(diagnosis_path.read_text(encoding="utf-8"))
    payload["families"][0]["style_tokens"].append("missing_style_profile")
    diagnosis_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match="unknown style tokens"):
        load_medical_figure_family_catalog(catalog_root)


def test_catalog_files_stay_split_by_natural_boundaries() -> None:
    new_files = [
        CATALOG_ROOT / "index.json",
        CATALOG_ROOT / "ai_adaptation_policy.json",
        CATALOG_ROOT / "style_profiles.json",
        CATALOG_ROOT / "palette_tokens.json",
        CATALOG_ROOT / "qa_gates.json",
        CATALOG_ROOT / "external_sources.json",
        REPO_ROOT / "src" / "med_autoscience" / "medical_figure_family_catalog.py",
        Path(__file__),
    ]
    new_files.extend(sorted((CATALOG_ROOT / "categories").glob("*.json")))

    oversized = {
        path.relative_to(REPO_ROOT).as_posix(): len(path.read_text(encoding="utf-8").splitlines())
        for path in new_files
        if len(path.read_text(encoding="utf-8").splitlines()) > 500
    }
    assert oversized == {}
