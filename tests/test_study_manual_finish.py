from __future__ import annotations

import importlib
from pathlib import Path

from tests.study_runtime_test_helpers import (
    make_profile,
    write_auditable_current_package,
    write_study,
    write_submission_metadata_only_bundle,
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
    write_auditable_current_package(study_root)

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
    write_auditable_current_package(study_root)
    current_package_root = study_root / "manuscript" / "current_package"
    (current_package_root / "submission_checklist.json").unlink()
    (current_package_root / "submission_manifest.json").write_text("{}", encoding="utf-8")
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
        quest_root=profile.runtime_root / "001-risk",
    )

    assert contract is not None
    assert contract.status.value == "active"
    assert contract.compatibility_guard_only is True
    assert "投稿包里程碑" in contract.summary


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
    write_auditable_current_package(study_root)
    current_package_root = study_root / "manuscript" / "current_package"
    (current_package_root / "submission_checklist.json").unlink()
    (current_package_root / "submission_manifest.json").write_text("{}", encoding="utf-8")
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
        quest_root=profile.runtime_root / "001-risk",
    )

    assert contract is None


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
    write_auditable_current_package(study_root)
    current_package_root = study_root / "manuscript" / "current_package"
    (current_package_root / "submission_checklist.json").unlink()
    (current_package_root / "submission_manifest.json").write_text("{}", encoding="utf-8")
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
        quest_root=profile.runtime_root / "004-reporting",
    )

    assert contract is not None
    assert "投稿包里程碑" in contract.summary
