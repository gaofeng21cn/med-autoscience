from __future__ import annotations

import csv
import importlib
import json
from pathlib import Path

import yaml


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _write_study_fixture(tmp_path: Path) -> tuple[Path, Path]:
    study_root = tmp_path / "studies" / "obesity_multicenter_phenotype_atlas"
    paper_root = study_root / "paper"
    data_root = tmp_path / "data" / "datasets" / "master" / "v2026-05-09-cleaned"
    _write_csv(
        data_root / "data" / "analysis_dataset_qc_deidentified.csv",
        [
            "source",
            "source_label",
            "center_code",
            "center_name",
            "sex",
            "age",
            "bmi_final",
            "bmi_category_china",
            "waist_cm",
            "diabetes",
            "hypertension",
            "dyslipidemia",
            "sleep_apnea",
            "mafld",
            "phq9_total",
            "gad7_total",
        ],
        [
            {
                "source": "alliance",
                "source_label": "Alliance platform",
                "center_code": "43A01",
                "center_name": "中南大学湘雅二医院",
                "sex": "1",
                "age": "35",
                "bmi_final": "31.2",
                "bmi_category_china": "Obesity",
                "waist_cm": "98",
                "diabetes": "1",
                "hypertension": "0",
                "dyslipidemia": "1",
                "sleep_apnea": "0",
                "mafld": "1",
                "phq9_total": "8",
                "gad7_total": "6",
            },
            {
                "source": "management",
                "source_label": "Xiangya2 management clinic",
                "center_code": "43A01",
                "center_name": "中南大学湘雅二医院",
                "sex": "0",
                "age": "42",
                "bmi_final": "28.5",
                "bmi_category_china": "Overweight",
                "waist_cm": "90",
                "diabetes": "0",
                "hypertension": "1",
                "dyslipidemia": "0",
                "sleep_apnea": "1",
                "mafld": "1",
                "phq9_total": "3",
                "gad7_total": "",
            },
            {
                "source": "precision",
                "source_label": "Xiangya2 precision clinic",
                "center_code": "43B02",
                "center_name": "Other center",
                "sex": "1",
                "age": "29",
                "bmi_final": "24.0",
                "bmi_category_china": "Normal",
                "waist_cm": "",
                "diabetes": "0",
                "hypertension": "0",
                "dyslipidemia": "0",
                "sleep_apnea": "0",
                "mafld": "0",
                "phq9_total": "",
                "gad7_total": "2",
            },
        ],
    )
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text(
        yaml.safe_dump(
            {
                "study_id": "obesity_multicenter_phenotype_atlas",
                "study_archetype": "clinical_subtype_reconstruction",
                "manuscript_family": "clinical_observation",
                "endpoint_type": "descriptive",
                "data_management_policy": {
                    "canonical_interchange_table": "../../data/datasets/master/v2026-05-09-cleaned/data/analysis_dataset_qc_deidentified.csv",
                    "data_dictionary": "../../data/datasets/master/v2026-05-09-cleaned/dictionary/data_dictionary.csv",
                    "quality_report": "../../data/datasets/master/v2026-05-09-cleaned/reports/quality_report.json",
                },
                "truth_surface_policy": {
                    "redlines": [
                        "do_not_claim_hunan_population_prevalence",
                        "do_not_claim_treatment_effect_or_weight_loss_efficacy",
                    ],
                },
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    _write_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _write_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    _write_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "cohort_flow",
            "catalog_id": "F1",
            "steps": [
                {"step_id": "source", "label": "Source records", "n": 3},
                {"step_id": "analysis", "label": "Analytic records", "n": 3},
            ],
        },
    )
    return study_root, paper_root


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.descriptive_registry_evidence_materializer")
    study_root, paper_root = _write_study_fixture(tmp_path)

    result = module.materialize_descriptive_registry_evidence(
        study_root=study_root,
        paper_root=paper_root,
        apply=False,
    )

    assert result["status"] == "planned"
    assert result["written_files"] == []
    assert not (paper_root / "baseline_characteristics_schema.json").exists()
    assert not (paper_root / "tables" / "T2_phenotype_gap_summary.csv").exists()


def test_apply_writes_tables_registry_and_closes_charter_expectations(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.descriptive_registry_evidence_materializer")
    study_root, paper_root = _write_study_fixture(tmp_path)

    result = module.materialize_descriptive_registry_evidence(
        study_root=study_root,
        paper_root=paper_root,
        apply=True,
    )

    assert result["status"] == "materialized"
    registry_text = (paper_root / "display_registry.json").read_text(encoding="utf-8")
    assert "F1_cohort_flow" not in registry_text
    registry = json.loads(registry_text)
    assert [(item["catalog_id"], item["requirement_key"]) for item in registry["displays"]] == [
        ("F1", "cohort_flow_figure"),
        ("T1", "table1_baseline_characteristics"),
        ("T2", "table2_phenotype_gap_summary"),
        ("T3", "table3_transition_site_support_summary"),
    ]
    for relpath in (
        "baseline_characteristics_schema.json",
        "cohort_flow.json",
        "phenotype_gap_summary_schema.json",
        "transition_site_support_summary_schema.json",
        "tables/T2_phenotype_gap_summary.csv",
        "tables/T3_transition_site_support_summary.csv",
        "figures/cohort_flow.shell.json",
        "tables/baseline_characteristics.shell.json",
        "tables/phenotype_gap_summary.shell.json",
        "tables/transition_site_support_summary.shell.json",
        "results_narrative_map.json",
    ):
        assert (paper_root / relpath).is_file()
    figure_shell = json.loads((paper_root / "figures" / "cohort_flow.shell.json").read_text(encoding="utf-8"))
    assert figure_shell["display_id"] == "cohort_flow"
    assert figure_shell["catalog_id"] == "F1"
    assert figure_shell["requirement_key"] == "cohort_flow_figure"
    cohort_flow = json.loads((paper_root / "cohort_flow.json").read_text(encoding="utf-8"))
    assert cohort_flow["flow_mode"] == "source_layer_accounting"
    assert cohort_flow["denominator_step_id"] == "registry_records"
    assert cohort_flow["steps"][0]["n"] == 3
    assert [item["n"] for item in cohort_flow["source_layers"]] == [1, 1, 1]
    assert cohort_flow["subcohort_coverage"] == [
        {
            "coverage_id": "xiangya2_subcohort",
            "label": "Xiangya Second Hospital subcohort",
            "detail": "Management and precision clinic records.",
            "n": 3,
            "denominator_n": 3,
        },
        {
            "coverage_id": "phq9_available",
            "label": "PHQ-9 available",
            "detail": "Psychobehavioral availability within the Xiangya2 subcohort.",
            "n": 2,
            "denominator_n": 3,
        },
        {
            "coverage_id": "gad7_available",
            "label": "GAD-7 available",
            "detail": "Psychobehavioral availability within the Xiangya2 subcohort.",
            "n": 2,
            "denominator_n": 3,
        },
    ]
    assert cohort_flow["exported_centers"] == 2
    ledger = json.loads((paper_root / "evidence_ledger.json").read_text(encoding="utf-8"))
    closed = {
        item["expectation_text"]: item["status"]
        for item in ledger["charter_expectation_closures"]
    }
    assert closed["table1_baseline_characteristics"] == "closed"
    assert closed["center_completeness_summary"] == "closed"
    assert closed["bmi_metabolic_comorbidity_burden"] == "closed"
    assert closed["xiangya2_psychobehavioral_subcohort_analysis"] == "closed"
    assert ledger["controller_repair_receipts"][0]["controller"] == "descriptive_registry_evidence_materializer"
    assert ledger["controller_repair_receipts"][0]["current_package_write_allowed"] is False


def test_materialized_contracts_satisfy_current_reporting_and_publication_validators(tmp_path: Path) -> None:
    materializer = importlib.import_module("med_autoscience.controllers.descriptive_registry_evidence_materializer")
    reporting_policy = importlib.import_module("med_autoscience.policies.medical_reporting_checklist")
    publication_policy = importlib.import_module("med_autoscience.policies.medical_publication_surface")
    catalog_checks = importlib.import_module("med_autoscience.controllers.medical_publication_surface.catalog_checks")
    study_root, paper_root = _write_study_fixture(tmp_path)

    materializer.materialize_descriptive_registry_evidence(study_root=study_root, paper_root=paper_root, apply=True)

    reporting_contract = json.loads((paper_root / "medical_reporting_contract.json").read_text(encoding="utf-8"))
    reporting_guideline_checklist = json.loads(
        (paper_root / "reporting_guideline_checklist.json").read_text(encoding="utf-8")
    )
    table_figure_claim_map = json.loads((paper_root / "table_figure_claim_map.json").read_text(encoding="utf-8"))
    structured_checklist = reporting_policy.build_structured_reporting_checklist(
        reporting_contract,
        reporting_closure=reporting_guideline_checklist,
        table_figure_claim_map=table_figure_claim_map,
    )
    assert structured_checklist["blockers"] == []
    assert structured_checklist["clinical_actionability"]["status"] == "clear"
    assert structured_checklist["treatment_gap_reporting"]["status"] == "clear"
    assert structured_checklist["manuscript_voice_reporting"]["status"] == "clear"

    evidence_ledger = json.loads((paper_root / "evidence_ledger.json").read_text(encoding="utf-8"))
    assert publication_policy.validate_evidence_ledger(evidence_ledger) == []
    assert all(claim["gaps"] for claim in evidence_ledger["claims"])
    assert all(claim["recommended_actions"] for claim in evidence_ledger["claims"])

    results_narrative_map = json.loads((paper_root / "results_narrative_map.json").read_text(encoding="utf-8"))
    assert publication_policy.validate_results_narrative_map(results_narrative_map) == []
    display_story_roles = catalog_checks.load_display_catalog_story_roles(paper_root / "medical_reporting_contract.json")
    assert catalog_checks.inspect_results_display_surface_coverage(
        path=paper_root / "results_narrative_map.json",
        payload=results_narrative_map,
        display_story_roles=display_story_roles,
    ) == []


def test_materialized_tables_are_consumed_by_display_surface_renderer(tmp_path: Path) -> None:
    materializer = importlib.import_module("med_autoscience.controllers.descriptive_registry_evidence_materializer")
    display_materializer = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    study_root, paper_root = _write_study_fixture(tmp_path)
    materializer.materialize_descriptive_registry_evidence(study_root=study_root, paper_root=paper_root, apply=True)
    registry = json.loads((paper_root / "display_registry.json").read_text(encoding="utf-8"))
    registry["displays"] = [item for item in registry["displays"] if item["display_kind"] == "table"]
    _write_json(paper_root / "display_registry.json", registry)

    result = display_materializer.materialize_display_surface(paper_root=paper_root)

    assert result["tables_materialized"] == ["T1", "T2", "T3"]
    assert (paper_root / "tables" / "generated" / "T1_baseline_characteristics.csv").is_file()
    assert (paper_root / "tables" / "generated" / "T2_phenotype_gap_summary.csv").is_file()
    assert (paper_root / "tables" / "generated" / "T3_transition_site_support_summary.csv").is_file()
    t3_header = (paper_root / "tables" / "generated" / "T3_transition_site_support_summary.csv").read_text(
        encoding="utf-8"
    ).splitlines()[0]
    assert t3_header == "Domain,Measure,Value"


def test_materialized_reporting_audit_accepts_cohort_flow_shell(tmp_path: Path) -> None:
    materializer = importlib.import_module("med_autoscience.controllers.descriptive_registry_evidence_materializer")
    reporting_audit = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    study_root, paper_root = _write_study_fixture(tmp_path)
    quest_root = tmp_path / "runtime" / "quests" / "obesity_multicenter_phenotype_atlas"
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(
        "quest_id: obesity_multicenter_phenotype_atlas\nstudy_id: obesity_multicenter_phenotype_atlas\n",
        encoding="utf-8",
    )
    (study_root / "runtime_binding.yaml").write_text(
        "quest_id: obesity_multicenter_phenotype_atlas\nstudy_id: obesity_multicenter_phenotype_atlas\n",
        encoding="utf-8",
    )
    _write_json(paper_root / "paper_bundle_manifest.json", {"schema_version": 1, "paper_branch": "paper/main"})
    (paper_root / "draft.md").write_text("# Draft\n\nDescriptive registry atlas.\n", encoding="utf-8")
    _write_json(paper_root / "medical_manuscript_blueprint.json", {"schema_version": 1})
    _write_json(paper_root / "medical_prose_review.json", {"schema_version": 1})
    _write_json(paper_root / "results_narrative_map.json", {"schema_version": 1})
    _write_json(paper_root / "figure_semantics_manifest.json", {"schema_version": 1})

    materializer.materialize_descriptive_registry_evidence(study_root=study_root, paper_root=paper_root, apply=True)
    result = reporting_audit.run_controller(quest_root=quest_root, apply=False)

    assert "missing_cohort_flow_shell" not in result["blockers"]
    assert "missing_cohort_flow" not in result["blockers"]
