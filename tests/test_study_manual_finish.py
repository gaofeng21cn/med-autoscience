from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import (
    make_profile,
    write_auditable_current_package,
    write_synced_submission_delivery,
    write_study,
    write_submission_metadata_only_bundle,
    write_text,
)


def test_resolve_effective_study_manual_finish_contract_prefers_explicit_study_yaml(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.study_manual_finish")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    study_yaml_path = study_root / "study.yaml"
    study_yaml_path.write_text(
        study_yaml_path.read_text(encoding="utf-8")
        + "\n".join(
            [
                "",
                "manual_finish:",
                "  status: active",
                "  summary: 当前 study 进入显式人工收尾。",
                "  next_action_summary: 等待人工完成最后核对。",
                "  compatibility_guard_only: true",
                "",
            ]
        ),
        encoding="utf-8",
    )
    quest_root = profile.runtime_root / "001-risk"
    write_submission_metadata_only_bundle(quest_root, blocking_item_ids=["author_metadata"])
    write_auditable_current_package(study_root)

    contract = module.resolve_effective_study_manual_finish_contract(
        study_root=study_root,
        quest_root=quest_root,
    )

    assert contract is not None
    assert contract.summary == "当前 study 进入显式人工收尾。"
    assert contract.next_action_summary == "等待人工完成最后核对。"


def test_resolve_effective_study_manual_finish_contract_derives_submission_metadata_only_parking(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_manual_finish")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.runtime_root / "001-risk"
    write_submission_metadata_only_bundle(
        quest_root,
        blocking_item_ids=["author_metadata", "ethics_statement"],
    )
    write_synced_submission_delivery(study_root, quest_root)

    contract = module.resolve_effective_study_manual_finish_contract(
        study_root=study_root,
        quest_root=quest_root,
    )

    assert contract is not None
    assert contract.status.value == "active"
    assert contract.compatibility_guard_only is True
    assert "系统已停车" in contract.summary


def test_resolve_effective_study_manual_finish_contract_derives_bundle_only_submission_ready_parking(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_manual_finish")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.runtime_root / "001-risk"
    write_synced_submission_delivery(
        study_root,
        quest_root,
        include_submission_checklist=False,
    )
    current_package_root = study_root / "manuscript" / "current_package"
    summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        "{\n"
        '  "quality_closure_truth": {"state": "bundle_only_remaining"},\n'
        '  "quality_assessment": {"human_review_readiness": {"status": "ready"}}\n'
        "}\n",
        encoding="utf-8",
    )

    contract = module.resolve_effective_study_manual_finish_contract(
        study_root=study_root,
        quest_root=quest_root,
    )

    assert contract is not None
    assert contract.status.value == "active"
    assert contract.compatibility_guard_only is True
    assert "投稿包里程碑" in contract.summary


def test_resolve_effective_study_manual_finish_contract_rejects_stale_bundle_only_submission_package(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_manual_finish")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.runtime_root / "001-risk"
    write_synced_submission_delivery(
        study_root,
        quest_root,
        include_submission_checklist=False,
        stale_authority_input=True,
    )
    summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        "{\n"
        '  "quality_closure_truth": {"state": "bundle_only_remaining"},\n'
        '  "quality_assessment": {"human_review_readiness": {"status": "ready"}}\n'
        "}\n",
        encoding="utf-8",
    )

    contract = module.resolve_effective_study_manual_finish_contract(
        study_root=study_root,
        quest_root=quest_root,
    )

    assert contract is None


def test_resolve_effective_study_manual_finish_contract_suppresses_auto_parking_for_reopened_revision(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_manual_finish")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.runtime_root / "001-risk"
    write_synced_submission_delivery(
        study_root,
        quest_root,
        include_submission_checklist=False,
    )
    summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        "{\n"
        '  "quality_closure_truth": {"state": "bundle_only_remaining"},\n'
        '  "quality_assessment": {"human_review_readiness": {"status": "ready"}}\n'
        "}\n",
        encoding="utf-8",
    )
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        entry_mode="full_research",
        task_intent=(
            "按最新专家意见重新打开同一论文线的修订任务；当前稿件不能按已达投稿包里程碑直接收口，"
            "并把当前 submission-ready/finalize 判断降回待修订后再评估。"
        ),
        constraints=("本轮不得直接按外投收口。",),
        first_cycle_outputs=("补充分层统计分析并写回 manuscript。",),
    )

    contract = module.resolve_effective_study_manual_finish_contract(
        study_root=study_root,
        quest_root=quest_root,
    )

    assert contract is None


def test_resolve_effective_study_manual_finish_contract_restores_bundle_only_parking_after_fresh_closeout(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_manual_finish")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.runtime_root / "001-risk"
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        entry_mode="full_research",
        task_intent=(
            "按最新专家意见重新打开同一论文线的修订任务；当前稿件不能按已达投稿包里程碑直接收口，"
            "并把当前 submission-ready/finalize 判断降回待修订后再评估。"
        ),
        constraints=("本轮不得直接按外投收口。",),
        first_cycle_outputs=("补充分层统计分析并写回 manuscript。",),
    )
    write_synced_submission_delivery(
        study_root,
        quest_root,
        include_submission_checklist=False,
    )
    summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        "{\n"
        '  "emitted_at": "2099-01-01T00:00:00+00:00",\n'
        '  "quality_closure_truth": {"state": "bundle_only_remaining", "current_required_action": "continue_bundle_stage"},\n'
        '  "quality_review_loop": {"closure_state": "bundle_only_remaining"},\n'
        '  "quality_assessment": {"human_review_readiness": {"status": "ready"}}\n'
        "}\n",
        encoding="utf-8",
    )

    contract = module.resolve_effective_study_manual_finish_contract(
        study_root=study_root,
        quest_root=quest_root,
    )

    assert contract is not None
    assert "投稿包里程碑" in contract.summary


def test_resolve_effective_study_manual_finish_contract_keeps_reporting_only_milestone_parking(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_manual_finish")
    task_intake_module = importlib.import_module("med_autoscience.study_task_intake")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "004-reporting",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.runtime_root / "004-reporting"
    write_synced_submission_delivery(
        study_root,
        quest_root,
        include_submission_checklist=False,
    )
    summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        "{\n"
        '  "quality_closure_truth": {"state": "bundle_only_remaining"},\n'
        '  "quality_assessment": {"human_review_readiness": {"status": "ready"}}\n'
        "}\n",
        encoding="utf-8",
    )
    task_intake_module.write_task_intake(
        profile=profile,
        study_id="004-reporting",
        study_root=study_root,
        entry_mode="full_research",
        task_intent=(
            "Repair the medical reporting/display contract mismatch. Do not reopen manuscript evidence adequacy, "
            "do not expand public data, and do not change scientific claims."
        ),
        constraints=("Keep route non-final write/review; do not treat gate clear or bundle presence as quest completion.",),
    )

    contract = module.resolve_effective_study_manual_finish_contract(
        study_root=study_root,
        quest_root=quest_root,
    )

    assert contract is not None
    assert "投稿包里程碑" in contract.summary


def test_resolve_effective_study_manual_finish_contract_accepts_delivered_current_package_with_admin_todo(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_manual_finish")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-attribution",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="clinical_epidemiology",
    )
    quest_root = profile.runtime_root / "002-attribution"
    current_package_root = study_root / "manuscript" / "current_package"
    current_package_root.mkdir(parents=True, exist_ok=True)
    write_text(current_package_root / "manuscript.docx", "docx placeholder")
    write_text(current_package_root / "paper.pdf", "pdf placeholder")
    write_text(current_package_root / "references.bib", "@article{ref1,title={Ref}}\n")
    write_text(current_package_root / "figures" / "Figure1.png", "figure placeholder")
    write_text(current_package_root / "tables" / "Table1.csv", "a,b\n1,2\n")
    write_text(
        current_package_root / "submission_manifest.json",
        json.dumps(
            {
                "schema_version": 1,
                "publication_profile": "general_medical_journal",
                "manuscript": {
                    "docx_path": "paper/submission_minimal/manuscript.docx",
                    "pdf_path": "paper/submission_minimal/paper.pdf",
                    "surface_qc": {"status": "pass", "failures": []},
                },
                "figures": [{"figure_id": "F1", "output_paths": ["paper/submission_minimal/figures/Figure1.png"]}],
                "tables": [{"table_id": "T1", "output_paths": ["paper/submission_minimal/tables/Table1.csv"]}],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        current_package_root / "SUBMISSION_TODO.md",
        "# Submission TODO\n\n"
        "Pending items:\n"
        "- Affiliations: pending\n"
        "- Authors: pending\n"
        "- Ethics approval number: pending\n"
        "- Funding: pending\n"
        "- Conflict of interest: pending\n"
        "- Data availability: pending\n",
    )
    write_text(study_root / "manuscript" / "current_package.zip", "zip placeholder")

    contract = module.resolve_effective_study_manual_finish_contract(
        study_root=study_root,
        quest_root=quest_root,
    )

    assert contract is not None
    assert contract.status.value == "active"
    assert contract.compatibility_guard_only is True
    assert "投稿包里程碑" in contract.summary


def test_resolve_effective_study_manual_finish_contract_rejects_delivered_package_with_scientific_todo(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_manual_finish")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-attribution",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="clinical_epidemiology",
    )
    package_root = study_root / "manuscript" / "current_package"
    package_root.mkdir(parents=True, exist_ok=True)
    write_text(package_root / "manuscript.docx", "docx placeholder")
    write_text(package_root / "paper.pdf", "pdf placeholder")
    write_text(package_root / "figures" / "Figure1.png", "figure placeholder")
    write_text(package_root / "tables" / "Table1.csv", "a,b\n1,2\n")
    write_text(
        package_root / "submission_manifest.json",
        json.dumps(
            {
                "schema_version": 1,
                "manuscript": {"surface_qc": {"status": "pass", "failures": []}},
                "figures": [{"figure_id": "F1"}],
                "tables": [{"table_id": "T1"}],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(package_root / "SUBMISSION_TODO.md", "# Submission TODO\n\n- Revise statistical analysis: pending\n")
    write_text(study_root / "manuscript" / "current_package.zip", "zip placeholder")

    contract = module.resolve_effective_study_manual_finish_contract(
        study_root=study_root,
        quest_root=profile.runtime_root / "002-attribution",
    )

    assert contract is None


def test_resolve_effective_study_manual_finish_contract_accepts_legacy_submission_package(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_manual_finish")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-legacy",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="clinical_epidemiology",
    )
    package_root = study_root / "manuscript" / "submission_package"
    package_root.mkdir(parents=True, exist_ok=True)
    write_text(package_root / "manuscript.docx", "docx placeholder")
    write_text(package_root / "paper.pdf", "pdf placeholder")
    write_text(package_root / "figures" / "Figure1.png", "figure placeholder")
    write_text(package_root / "tables" / "Table1.csv", "a,b\n1,2\n")
    manifest = {
        "schema_version": 1,
        "publication_profile": "frontiers_family_harvard",
        "manuscript": {"docx_path": "paper/journal_submissions/frontiers/manuscript.docx", "pdf_path": "paper/journal_submissions/frontiers/paper.pdf"},
        "figures": [{"figure_id": "F1", "output_paths": ["paper/journal_submissions/frontiers/figures/Figure1.png"]}],
        "tables": [{"table_id": "T1", "output_paths": ["paper/journal_submissions/frontiers/tables/Table1.csv"]}],
    }
    write_text(package_root / "submission_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    write_text(study_root / "manuscript" / "submission_manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    contract = module.resolve_effective_study_manual_finish_contract(
        study_root=study_root,
        quest_root=profile.runtime_root / "002-legacy",
    )

    assert contract is not None
    assert "投稿包里程碑" in contract.summary
