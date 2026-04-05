from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_medical_reporting_audit_blocks_missing_cohort_flow_surface(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    (quest_root / "paper").mkdir(parents=True, exist_ok=True)
    (quest_root / "paper" / "medical_reporting_contract.json").write_text(
        '{"reporting_guideline_family": "TRIPOD"}',
        encoding="utf-8",
    )

    report = module.run_controller(quest_root=quest_root, apply=False)

    assert report["status"] == "blocked"
    assert "missing_cohort_flow" in report["blockers"]
    assert "missing_baseline_characteristics_schema" in report["blockers"]
    assert "missing_reporting_guideline_checklist" in report["blockers"]


def test_medical_reporting_audit_apply_writes_reporting_guideline_checklist(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    paper_root = quest_root / "paper"
    (paper_root / "figures").mkdir(parents=True, exist_ok=True)
    (paper_root / "tables").mkdir(parents=True, exist_ok=True)

    display_plan = [
        {
            "display_id": "cohort_flow",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "catalog_id": "F1",
        },
        {
            "display_id": "baseline_characteristics",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
            "catalog_id": "T1",
        },
    ]
    (paper_root / "medical_reporting_contract.json").write_text(
        json.dumps(
            {
                "reporting_guideline_family": "TRIPOD",
                "display_registry_required": True,
                "display_shell_plan": display_plan,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "display_registry.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_contract_path": "paper/medical_reporting_contract.json",
                "displays": [
                    {
                        **item,
                        "shell_path": (
                            f"paper/figures/{item['display_id']}.shell.json"
                            if item["display_kind"] == "figure"
                            else f"paper/tables/{item['display_id']}.shell.json"
                        ),
                    }
                    for item in display_plan
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "figures" / "cohort_flow.shell.json").write_text("{}", encoding="utf-8")
    (paper_root / "tables" / "baseline_characteristics.shell.json").write_text("{}", encoding="utf-8")
    (paper_root / "cohort_flow.json").write_text("{}", encoding="utf-8")
    (paper_root / "baseline_characteristics_schema.json").write_text("{}", encoding="utf-8")

    report = module.run_controller(quest_root=quest_root, apply=True)

    checklist = json.loads((paper_root / "reporting_guideline_checklist.json").read_text(encoding="utf-8"))
    assert report["status"] == "clear"
    assert report["blockers"] == []
    assert checklist["reporting_guideline_family"] == "TRIPOD"
    assert checklist["required_display_count"] == 2


def test_write_audit_files_uses_runtime_protocol_report_store(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    seen: dict[str, object] = {}

    def fake_write_timestamped_report(
        *,
        quest_root: Path,
        report_group: str,
        timestamp: str,
        report: dict[str, object],
        markdown: str,
    ) -> tuple[Path, Path]:
        seen["quest_root"] = quest_root
        seen["report_group"] = report_group
        seen["timestamp"] = timestamp
        seen["report"] = report
        seen["markdown"] = markdown
        return (
            quest_root / "artifacts" / "reports" / report_group / "latest.json",
            quest_root / "artifacts" / "reports" / report_group / "latest.md",
        )

    monkeypatch.setattr(module.runtime_protocol_report_store, "write_timestamped_report", fake_write_timestamped_report)

    report = {
        "generated_at": "2026-04-03T10:00:00+00:00",
        "quest_root": str(quest_root),
        "status": "blocked",
        "blockers": ["missing_cohort_flow"],
        "action": "clear",
    }

    json_path, md_path = module.write_audit_files(quest_root, report)

    assert seen["quest_root"] == quest_root
    assert seen["report_group"] == "medical_reporting_audit"
    assert seen["timestamp"] == "2026-04-03T10:00:00+00:00"
    assert json_path.name == "latest.json"
    assert md_path.name == "latest.md"


def test_medical_reporting_audit_reads_active_worktree_paper_root(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk-reentry"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-main" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    (paper_root / "paper_bundle_manifest.json").write_text("{}", encoding="utf-8")
    (paper_root / "medical_reporting_contract.json").write_text(
        '{"reporting_guideline_family": "TRIPOD"}',
        encoding="utf-8",
    )

    report = module.run_controller(quest_root=quest_root, apply=False)

    assert report["status"] == "blocked"
    assert "missing_medical_reporting_contract" not in report["blockers"]
    assert "missing_cohort_flow" in report["blockers"]


def test_medical_reporting_audit_blocks_missing_direct_migration_stub(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_reporting_audit")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    paper_root = quest_root / "paper"
    (paper_root / "figures").mkdir(parents=True, exist_ok=True)
    (paper_root / "tables").mkdir(parents=True, exist_ok=True)

    display_plan = [
        {
            "display_id": "cohort_flow",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "catalog_id": "F1",
        },
        {
            "display_id": "discrimination_calibration",
            "display_kind": "figure",
            "requirement_key": "time_to_event_discrimination_calibration_panel",
            "catalog_id": "F2",
        },
        {
            "display_id": "km_risk_stratification",
            "display_kind": "figure",
            "requirement_key": "kaplan_meier_grouped",
            "catalog_id": "F3",
        },
        {
            "display_id": "decision_curve",
            "display_kind": "figure",
            "requirement_key": "time_to_event_decision_curve",
            "catalog_id": "F4",
        },
        {
            "display_id": "multicenter_generalizability",
            "display_kind": "figure",
            "requirement_key": "multicenter_generalizability_overview",
            "catalog_id": "F5",
        },
        {
            "display_id": "baseline_characteristics",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
            "catalog_id": "T1",
        },
        {
            "display_id": "time_to_event_performance_summary",
            "display_kind": "table",
            "requirement_key": "table2_time_to_event_performance_summary",
            "catalog_id": "T2",
        },
    ]
    (paper_root / "medical_reporting_contract.json").write_text(
        json.dumps(
            {
                "reporting_guideline_family": "TRIPOD",
                "display_registry_required": True,
                "display_shell_plan": display_plan,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "display_registry.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "source_contract_path": "paper/medical_reporting_contract.json",
                "displays": [
                    {
                        **item,
                        "shell_path": (
                            f"paper/figures/{item['display_id']}.shell.json"
                            if item["display_kind"] == "figure"
                            else f"paper/tables/{item['display_id']}.shell.json"
                        ),
                    }
                    for item in display_plan
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    for item in display_plan:
        shell_path = (
            paper_root / "figures" / f"{item['display_id']}.shell.json"
            if item["display_kind"] == "figure"
            else paper_root / "tables" / f"{item['display_id']}.shell.json"
        )
        shell_path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "source_contract_path": "paper/medical_reporting_contract.json",
                    "display_id": item["display_id"],
                    "display_kind": item["display_kind"],
                    "requirement_key": item["requirement_key"],
                    "catalog_id": item["catalog_id"],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    (paper_root / "cohort_flow.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "shell_id": "cohort_flow_figure",
                "display_id": "cohort_flow",
                "catalog_id": "F1",
                "source_contract_path": "paper/medical_reporting_contract.json",
                "status": "required_pending_cohort_flow_materialization",
                "steps": [],
                "exclusions": [],
                "endpoint_inventory": [],
                "design_panels": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "baseline_characteristics_schema.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "table_shell_id": "table1_baseline_characteristics",
                "display_id": "baseline_characteristics",
                "catalog_id": "T1",
                "source_contract_path": "paper/medical_reporting_contract.json",
                "status": "required_pending_table_materialization",
                "group_columns": [],
                "variables": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "time_to_event_performance_summary.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "table_shell_id": "table2_time_to_event_performance_summary",
                "display_id": "time_to_event_performance_summary",
                "catalog_id": "T2",
                "source_contract_path": "paper/medical_reporting_contract.json",
                "status": "required_pending_materialization",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "time_to_event_discrimination_calibration_inputs.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "input_schema_id": "time_to_event_discrimination_calibration_inputs_v1",
                "source_contract_path": "paper/medical_reporting_contract.json",
                "status": "required_pending_materialization",
                "displays": [
                    {
                        "display_id": "discrimination_calibration",
                        "catalog_id": "F2",
                        "template_id": "time_to_event_discrimination_calibration_panel",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "time_to_event_grouped_inputs.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "input_schema_id": "time_to_event_grouped_inputs_v1",
                "source_contract_path": "paper/medical_reporting_contract.json",
                "status": "required_pending_materialization",
                "displays": [
                    {
                        "display_id": "km_risk_stratification",
                        "catalog_id": "F3",
                        "template_id": "kaplan_meier_grouped",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "time_to_event_decision_curve_inputs.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "input_schema_id": "time_to_event_decision_curve_inputs_v1",
                "source_contract_path": "paper/medical_reporting_contract.json",
                "status": "required_pending_materialization",
                "displays": [
                    {
                        "display_id": "decision_curve",
                        "catalog_id": "F4",
                        "template_id": "time_to_event_decision_curve",
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (paper_root / "reporting_guideline_checklist.json").write_text("{}", encoding="utf-8")

    report = module.run_controller(quest_root=quest_root, apply=False)

    assert report["status"] == "blocked"
    assert report["blockers"] == ["missing_multicenter_generalizability_inputs"]
