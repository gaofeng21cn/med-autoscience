from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_reviewer_revision_intake_yields_to_ai_reviewer_quality_closure_after_verified_handoff(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")
    study_root = tmp_path / "studies" / "003-endocrine-burden-followup"
    payload = {
        "task_id": "study-task::003-endocrine-burden-followup::20260426T065318Z",
        "emitted_at": "2026-04-26T06:53:18+00:00",
        "task_intent": "Revise the manuscript after reviewer feedback and write manuscript revision outputs back.",
        "first_cycle_outputs": [
            "当前最新 task intake 指定的首轮修订产出是否已经补齐并写回 manuscript？"
        ],
    }
    gate_report = {
        "generated_at": "2026-04-27T02:02:40+00:00",
        "status": "clear",
        "allow_write": True,
        "blockers": [],
        "current_required_action": "continue_bundle_stage",
    }
    evaluation_summary = {
        "emitted_at": "2026-04-27T02:02:52+00:00",
        "promotion_gate_status": {
            "status": "clear",
            "allow_write": True,
            "current_required_action": "continue_bundle_stage",
            "blockers": [],
        },
        "quality_closure_truth": {
            "state": "quality_repair_required",
            "summary": (
                "当前 publication_eval 只是机械投影；必须先由 AI reviewer 读取 manuscript、"
                "evidence ledger、review ledger 与 study charter 后再给出科学质量闭环判断。"
            ),
            "current_required_action": "continue_bundle_stage",
            "route_target": "finalize",
        },
        "quality_review_loop": {
            "closure_state": "quality_repair_required",
            "lane_id": "submission_hardening",
            "current_phase": "revision_required",
            "blocking_issues": ["缺少 assessment_provenance.owner=ai_reviewer 的当前质量判断。"],
            "next_review_focus": ["AI reviewer-backed publication_eval"],
            "recommended_next_action": (
                "先发起 AI reviewer 复评，并把 reviewer-authored assessment 写回 publication_eval。"
            ),
        },
    }

    stale_override = module.build_task_intake_progress_override(
        payload,
        study_root=study_root,
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    )
    assert stale_override is not None
    assert stale_override["paper_stage"] == "write"

    _write_json(
        study_root
        / "artifacts"
        / "controller"
        / "task_intake"
        / "revision_handoff_verification_20260427T0159Z.json",
        {
            "schema_version": 1,
            "verification_id": "revision-handoff-verification::003-endocrine-burden-followup::20260427T0159Z",
            "created_at": "2026-04-27T01:59:29Z",
            "source_task_id": "study-task::003-endocrine-burden-followup::20260426T065318Z",
            "answer": "yes_same_scope_revalidated_after_correcting_stale_auxiliary_balance_note",
            "boundary": {
                "not_first_cycle_writeback_blockers": True,
                "remaining_downstream_items": ["AI-reviewer-backed finalize-quality closure"],
            },
            "next_route": "close_write_stage_route_key_question_then_return_to_controller_supervised_finalize_or_bundle_hardening_closeout",
        },
    )

    assert module.build_task_intake_progress_override(
        payload,
        study_root=study_root,
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    ) is None


def test_reviewer_revision_intake_yields_to_verified_bundle_only_closeout_with_admin_open_items(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")
    study_root = tmp_path / "studies" / "003-endocrine-burden-followup"
    payload = {
        "task_id": "study-task::003-endocrine-burden-followup::20260426T065318Z",
        "emitted_at": "2026-04-26T06:53:18+00:00",
        "task_intent": "Revise the manuscript after reviewer feedback and write manuscript revision outputs back.",
        "first_cycle_outputs": [
            "当前最新 task intake 指定的首轮修订产出是否已经补齐并写回 manuscript？"
        ],
    }
    gate_report = {
        "generated_at": "2026-04-27T21:01:49+00:00",
        "status": "clear",
        "allow_write": True,
        "blockers": [],
        "current_required_action": "continue_bundle_stage",
    }
    evaluation_summary = {
        "emitted_at": "2026-04-27T21:03:00+00:00",
        "promotion_gate_status": {
            "status": "clear",
            "allow_write": True,
            "current_required_action": "continue_bundle_stage",
            "blockers": [],
        },
        "quality_closure_truth": {
            "state": "bundle_only_remaining",
            "current_required_action": "continue_bundle_stage",
            "route_target": "finalize",
        },
        "study_quality_truth": {
            "contract_closed": True,
            "narrowest_scientific_gap": {
                "state": "closed",
                "summary": "Open scientific gap is already closed; only finalize closeout remains.",
            },
            "reviewer_first": {
                "ready": False,
                "status": "blocked",
                "summary": (
                    "review ledger 仍有 2 个未关闭 concern，"
                    "but both are author/declaration metadata and post-metadata package audit."
                ),
            },
        },
        "quality_review_loop": {
            "closure_state": "bundle_only_remaining",
        },
        "quality_assessment": {
            "human_review_readiness": {
                "status": "ready",
            }
        },
    }

    stale_override = module.build_task_intake_progress_override(
        payload,
        study_root=study_root,
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    )
    assert stale_override is not None
    assert stale_override["paper_stage"] == "write"

    _write_json(
        study_root
        / "artifacts"
        / "controller"
        / "task_intake"
        / "revision_handoff_verification_20260427T2054Z.json",
        {
            "schema_version": 1,
            "record_type": "revision_handoff_verification",
            "created_at": "2026-04-27T20:54:33Z",
            "source_task_id": "study-task::003-endocrine-burden-followup::20260426T065318Z",
            "answer": "yes_first_cycle_revision_outputs_complete_and_written_back_to_manuscript",
            "task_intake_has_newer_superseding_task": False,
            "evidence": {
                "task_intake": {"newer_task_intake_found": False},
            },
            "boundary": {
                "not_first_cycle_writeback_blockers": True,
                "remaining_downstream_items": [
                    "external author/declaration metadata closeout",
                    "targeted package audit after metadata insertion",
                ],
            },
            "next_route": (
                "close_write_stage_route_key_question_then_return_to_controller_supervised_"
                "finalize_or_bundle_hardening_closeout"
            ),
        },
    )

    assert module.build_task_intake_progress_override(
        payload,
        study_root=study_root,
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    ) is None


def test_reviewer_revision_intake_yields_to_direct_table1_pvalue_completion(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")
    study_root = tmp_path / "studies" / "003-endocrine-burden-followup"
    payload = {
        "task_id": "study-task::003-endocrine-burden-followup::20260430T133517Z",
        "emitted_at": "2026-04-30T13:35:17+00:00",
        "task_intent": (
            "Revise Table 1 for the 003 NF-PitNET endocrine burden manuscript: add a p-value column comparing "
            "No persistent postoperative hypopituitarism versus Persistent postoperative hypopituitarism for each "
            "displayed baseline characteristic."
        ),
        "constraints": [
            "Do not change the endpoint, event count, cohort definition, model results, or claim boundary.",
            "P values are descriptive baseline comparisons for Table 1 only; they must not be introduced as model-selection evidence.",
        ],
        "trusted_inputs": [
            "User feedback on 2026-04-30: Table 1 currently lacks statistical comparison between the two persistent postoperative hypopituitarism groups and needs a p-value column."
        ],
        "first_cycle_outputs": [
            "Updated Table 1 CSV/Markdown in canonical paper source and refreshed submission/current_package surfaces."
        ],
    }
    gate_report = {
        "generated_at": "2026-05-03T12:49:34+00:00",
        "status": "clear",
        "allow_write": True,
        "blockers": [],
        "current_required_action": "continue_bundle_stage",
        "submission_minimal_authority_status": "current",
        "study_delivery_status": "current",
        "medical_publication_surface_status": "clear",
    }
    evaluation_summary = {
        "emitted_at": "2026-05-03T12:51:48+00:00",
        "promotion_gate_status": {
            "status": "clear",
            "allow_write": True,
            "current_required_action": "continue_bundle_stage",
            "blockers": [],
        },
        "quality_closure_truth": {
            "state": "quality_repair_required",
            "current_required_action": "return_to_ai_reviewer",
            "summary": "当前质量判断仍是机械投影，只能进入 AI reviewer review required。",
        },
        "study_quality_truth": {
            "contract_closed": False,
            "reviewer_first": {
                "ready": False,
                "status": "review_required",
                "summary": "publication_eval still requires AI reviewer authority.",
            },
        },
        "quality_review_loop": {
            "closure_state": "quality_repair_required",
            "blocking_issues": ["缺少 assessment_provenance.owner=ai_reviewer 的当前质量判断。"],
            "recommended_next_action": "补齐 AI reviewer workflow、publication eval 与 medical prose review。",
        },
        "quality_assessment": {"human_review_readiness": {"status": "ready"}},
    }

    stale_override = module.build_task_intake_progress_override(
        payload,
        study_root=study_root,
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    )
    assert stale_override is not None
    assert stale_override["paper_stage"] == "write"

    _write_json(
        study_root
        / "artifacts"
        / "controller"
        / "task_intake"
        / "direct_foreground_table1_pvalue_completion_20260430T1417Z.json",
        {
            "schema_version": 1,
            "event_id": "direct-foreground-table1-pvalue-completion-20260430T1417Z",
            "completed_at": "2026-04-30T14:17:00Z",
            "study_id": "003-endocrine-burden-followup",
            "user_directive": "Stop MAS/MDS and complete the narrow Table 1 p-value request directly.",
            "completed_scope": [
                "Added P value to Table 1 comparing the two postoperative hypopituitarism groups.",
                "Updated canonical generated Table 1 CSV/Markdown.",
                "Updated paper/submission_minimal Table 1 CSV/Markdown.",
                "Updated manuscript/current_package Table 1 CSV/Markdown.",
                "Updated current-package manuscript Markdown, DOCX, PDF, top-level manuscript mirrors, and current_package.zip.",
            ],
            "statistical_methods": {
                "continuous_or_ordinal": "two-sided Mann-Whitney U test",
                "binary": "two-sided Fisher exact test",
                "format_rule": "<0.001 if p<0.001, otherwise three decimals",
            },
            "unchanged_boundaries": [
                "endpoint",
                "cohort definition",
                "event count",
                "model results",
                "claim boundary",
            ],
        },
    )

    assert module.build_task_intake_progress_override(
        payload,
        study_root=study_root,
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    ) is None
