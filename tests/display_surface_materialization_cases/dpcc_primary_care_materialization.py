from .shared import *


def test_load_evidence_display_payload_accepts_dpcc_phenotype_gap_structure(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "dpcc_phenotype_gap_structure.json",
        {
            "schema_version": 1,
            "input_schema_id": "dpcc_phenotype_gap_structure_v1",
            "displays": [
                {
                    "display_id": "Figure2",
                    "template_id": full_id("phenotype_gap_structure_figure"),
                    "title": "Phenotype composition and treatment-gap profiles across the DPCC index cohort.",
                    "rows": [
                        {
                            "phenotype_label": "Phenotype A",
                            "share_of_index_patients": 0.42,
                            "severe_glycemia_low_intensity_gap_rate": 0.18,
                            "uncontrolled_glycemia_no_drug_gap_rate": 0.24,
                            "hypertension_no_antihypertensive_gap_rate": 0.16,
                            "dyslipidemia_no_lipid_lowering_gap_rate": 0.21,
                        },
                        {
                            "phenotype_label": "Phenotype B",
                            "share_of_index_patients": 0.58,
                            "severe_glycemia_low_intensity_gap_rate": 0.07,
                            "uncontrolled_glycemia_no_drug_gap_rate": 0.11,
                            "hypertension_no_antihypertensive_gap_rate": None,
                            "dyslipidemia_no_lipid_lowering_gap_rate": 0.14,
                        },
                    ],
                }
            ],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("phenotype_gap_structure_figure")
    payload_path, display_payload = module._load_evidence_display_payload(
        paper_root=paper_root,
        spec=spec,
        display_id="Figure2",
    )

    assert payload_path.name == "dpcc_phenotype_gap_structure.json"
    assert display_payload["template_id"] == full_id("phenotype_gap_structure_figure")
    assert [row["phenotype_label"] for row in display_payload["rows"]] == ["Phenotype A", "Phenotype B"]
    assert display_payload["rows"][1]["hypertension_no_antihypertensive_gap_rate"] is None


def test_load_evidence_display_payload_accepts_dpcc_transition_site_support(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "dpcc_transition_site_support.json",
        {
            "schema_version": 1,
            "input_schema_id": "dpcc_transition_site_support_v1",
            "displays": [
                {
                    "display_id": "Figure3",
                    "template_id": full_id("site_held_out_stability_figure"),
                    "title": "Transition stability and site-held-out support for phenotype assignment.",
                    "transition_rows": [
                        {
                            "source_phenotype_label": "Phenotype A",
                            "target_phenotype_label": "Phenotype A",
                            "patient_count": 84,
                            "share_of_transition_patients": 0.62,
                        },
                        {
                            "source_phenotype_label": "Phenotype A",
                            "target_phenotype_label": "Phenotype B",
                            "patient_count": 51,
                            "share_of_transition_patients": 0.38,
                        },
                        {
                            "source_phenotype_label": "Phenotype B",
                            "target_phenotype_label": "Phenotype B",
                            "patient_count": 93,
                            "share_of_transition_patients": 0.67,
                        },
                        {
                            "source_phenotype_label": "Phenotype B",
                            "target_phenotype_label": "Phenotype A",
                            "patient_count": 45,
                            "share_of_transition_patients": 0.33,
                        },
                    ],
                    "site_fold_rows": [
                        {
                            "fold_id": "fold_1",
                            "index_patients": 120,
                            "share_of_index_patients": 0.34,
                        },
                        {
                            "fold_id": "fold_2",
                            "index_patients": 111,
                            "share_of_index_patients": 0.31,
                        },
                        {
                            "fold_id": "pooled_small_site",
                            "index_patients": 121,
                            "share_of_index_patients": 0.35,
                        },
                    ],
                    "eligible_site_count": 6,
                    "visit_coverage": 0.83,
                }
            ],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("site_held_out_stability_figure")
    payload_path, display_payload = module._load_evidence_display_payload(
        paper_root=paper_root,
        spec=spec,
        display_id="Figure3",
    )

    assert payload_path.name == "dpcc_transition_site_support.json"
    assert display_payload["eligible_site_count"] == 6
    assert display_payload["visit_coverage"] == pytest.approx(0.83)
    assert len(display_payload["transition_rows"]) == 4
    assert len(display_payload["site_fold_rows"]) == 3


def test_load_evidence_display_payload_accepts_dpcc_treatment_gap_alignment(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "dpcc_treatment_gap_alignment.json",
        {
            "schema_version": 1,
            "input_schema_id": "dpcc_treatment_gap_alignment_v1",
            "displays": [
                {
                    "display_id": "Figure4",
                    "template_id": full_id("treatment_gap_alignment_figure"),
                    "title": "Guideline-linked treatment gaps aligned to the six DPCC phenotypes.",
                    "rows": [
                        {
                            "phenotype_label": "Phenotype A",
                            "index_patients": 320,
                            "severe_glycemia_low_intensity_gap_patients": 44,
                            "uncontrolled_glycemia_no_drug_gap_patients": 61,
                            "hypertension_no_antihypertensive_gap_patients": 37,
                            "dyslipidemia_no_lipid_lowering_gap_patients": 72,
                        },
                        {
                            "phenotype_label": "Phenotype B",
                            "index_patients": 280,
                            "severe_glycemia_low_intensity_gap_patients": 29,
                            "uncontrolled_glycemia_no_drug_gap_patients": 41,
                            "hypertension_no_antihypertensive_gap_patients": 18,
                            "dyslipidemia_no_lipid_lowering_gap_patients": 56,
                        },
                    ],
                }
            ],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("treatment_gap_alignment_figure")
    payload_path, display_payload = module._load_evidence_display_payload(
        paper_root=paper_root,
        spec=spec,
        display_id="Figure4",
    )

    assert payload_path.name == "dpcc_treatment_gap_alignment.json"
    assert display_payload["rows"][0]["index_patients"] == 320
    assert display_payload["rows"][0]["dyslipidemia_no_lipid_lowering_gap_patients"] == 72
    assert display_payload["rows"][1]["hypertension_no_antihypertensive_gap_patients"] == 18


@pytest.mark.parametrize(
    ("template_short_id", "display_payload", "expected_panel_count", "expected_metric_key"),
    [
        (
            "phenotype_gap_structure_figure",
            {
                "title": "Phenotype composition and treatment-gap profiles across the DPCC index cohort.",
                "rows": [
                    {
                        "phenotype_label": "Phenotype A",
                        "share_of_index_patients": 0.42,
                        "severe_glycemia_low_intensity_gap_rate": 0.18,
                        "uncontrolled_glycemia_no_drug_gap_rate": 0.24,
                        "hypertension_no_antihypertensive_gap_rate": 0.16,
                        "dyslipidemia_no_lipid_lowering_gap_rate": 0.21,
                    },
                    {
                        "phenotype_label": "Phenotype B",
                        "share_of_index_patients": 0.58,
                        "severe_glycemia_low_intensity_gap_rate": 0.07,
                        "uncontrolled_glycemia_no_drug_gap_rate": 0.11,
                        "hypertension_no_antihypertensive_gap_rate": None,
                        "dyslipidemia_no_lipid_lowering_gap_rate": 0.14,
                    },
                ],
            },
            2,
            "rows",
        ),
        (
            "site_held_out_stability_figure",
            {
                "title": "Transition stability and site-held-out support for phenotype assignment.",
                "transition_rows": [
                    {
                        "source_phenotype_label": "Phenotype A",
                        "target_phenotype_label": "Phenotype A",
                        "patient_count": 84,
                        "share_of_transition_patients": 0.62,
                    },
                    {
                        "source_phenotype_label": "Phenotype A",
                        "target_phenotype_label": "Phenotype B",
                        "patient_count": 51,
                        "share_of_transition_patients": 0.38,
                    },
                    {
                        "source_phenotype_label": "Phenotype B",
                        "target_phenotype_label": "Phenotype B",
                        "patient_count": 93,
                        "share_of_transition_patients": 0.67,
                    },
                    {
                        "source_phenotype_label": "Phenotype B",
                        "target_phenotype_label": "Phenotype A",
                        "patient_count": 45,
                        "share_of_transition_patients": 0.33,
                    },
                ],
                "site_fold_rows": [
                    {
                        "fold_id": "fold_1",
                        "index_patients": 120,
                        "share_of_index_patients": 0.34,
                    },
                    {
                        "fold_id": "fold_2",
                        "index_patients": 111,
                        "share_of_index_patients": 0.31,
                    },
                    {
                        "fold_id": "pooled_small_site",
                        "index_patients": 121,
                        "share_of_index_patients": 0.35,
                    },
                ],
                "eligible_site_count": 6,
                "visit_coverage": 0.83,
            },
            2,
            "transition_rows",
        ),
        (
            "treatment_gap_alignment_figure",
            {
                "title": "Guideline-linked treatment gaps aligned to the six DPCC phenotypes.",
                "rows": [
                    {
                        "phenotype_label": "Phenotype A",
                        "index_patients": 320,
                        "severe_glycemia_low_intensity_gap_patients": 44,
                        "uncontrolled_glycemia_no_drug_gap_patients": 61,
                        "hypertension_no_antihypertensive_gap_patients": 37,
                        "dyslipidemia_no_lipid_lowering_gap_patients": 72,
                    },
                    {
                        "phenotype_label": "Phenotype B",
                        "index_patients": 280,
                        "severe_glycemia_low_intensity_gap_patients": 29,
                        "uncontrolled_glycemia_no_drug_gap_patients": 41,
                        "hypertension_no_antihypertensive_gap_patients": 18,
                        "dyslipidemia_no_lipid_lowering_gap_patients": 56,
                    },
                ],
            },
            4,
            "panels",
        ),
    ],
)
def test_render_python_evidence_figure_materializes_dpcc_primary_care_templates(
    tmp_path: Path,
    template_short_id: str,
    display_payload: dict[str, object],
    expected_panel_count: int,
    expected_metric_key: str,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    output_png_path = tmp_path / f"{template_short_id}.png"
    output_pdf_path = tmp_path / f"{template_short_id}.pdf"
    layout_sidecar_path = tmp_path / f"{template_short_id}.layout.json"

    module._render_python_evidence_figure(
        template_id=full_id(template_short_id),
        display_payload=display_payload,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    assert output_png_path.exists()
    assert output_pdf_path.exists()
    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert layout_sidecar["template_id"] == template_short_id
    assert len(layout_sidecar["panel_boxes"]) == expected_panel_count
    assert layout_sidecar["metrics"][expected_metric_key]
