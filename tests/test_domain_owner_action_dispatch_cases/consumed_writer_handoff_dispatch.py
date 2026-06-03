from __future__ import annotations

import importlib
from pathlib import Path

from tests.domain_owner_action_dispatch_helpers import (
    dispatch as _dispatch,
    owner_route as _owner_route,
    write_json as _write_json,
)
from tests.study_runtime_test_helpers import make_profile, write_study


def test_execute_dispatch_does_not_execute_consumed_quality_repair_handoff_when_ai_reviewer_is_current(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_owner_action_dispatch")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=f"quest-{study_id}")
    dispatch_dir = study_root / "artifacts" / "supervision" / "consumer" / "default_executor_dispatches"

    ai_route = _owner_route(
        study_id=study_id,
        action_type="return_to_ai_reviewer_workflow",
        owner="ai_reviewer",
    )
    ai_route.update(
        {
            "truth_epoch": "truth-event-current-manuscript",
            "runtime_health_epoch": "",
            "work_unit_fingerprint": "truth-snapshot::current-manuscript",
            "source_fingerprint": "truth-snapshot::current-manuscript",
            "route_epoch": "truth-event-current-manuscript",
            "failure_signature": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            "owner_reason": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
            "source_refs": {
                "source_eval_id": "publication-eval::003::ai-reviewer-record::old",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_manuscript",
                "work_unit_fingerprint": "truth-snapshot::current-manuscript",
            },
            "idempotency_key": "owner-route::003::ai-reviewer::current-manuscript",
        }
    )
    writer_route = _owner_route(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
    )
    writer_route.update(
        {
            "truth_epoch": "publication-eval::003::ai-reviewer-record::old",
            "runtime_health_epoch": None,
            "work_unit_fingerprint": "publication-blockers::old-writer",
            "source_fingerprint": "publication-blockers::old-writer",
            "route_epoch": "quality-repair-writer-handoff::003::publication-eval::old",
            "failure_signature": "manuscript_story_surface_delta_missing",
            "owner_reason": "manuscript_story_surface_delta_missing",
            "source_refs": {
                "source_eval_id": "publication-eval::003::ai-reviewer-record::old",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::old-writer",
                "blocked_reason": "manuscript_story_surface_delta_missing",
            },
            "idempotency_key": "quality-repair-writer-handoff::003::publication-blockers::old-writer",
        }
    )

    writer_dispatch = _dispatch(
        study_id=study_id,
        action_type="run_quality_repair_batch",
        owner="write",
        required_output_surface=(
            "canonical manuscript story-surface delta or "
            "typed blocker:manuscript_story_surface_delta_missing"
        ),
        owner_route=writer_route,
    )
    writer_dispatch.update(
        {
            "dispatch_authority": "quality_repair_batch_writer_handoff",
            "action_id": "quality-repair-writer-handoff::003::publication-eval::old",
            "source_action": {
                "surface": "quality_repair_batch",
                "action_type": "run_quality_repair_batch",
                "blocked_reason": "manuscript_story_surface_delta_missing",
                "source_eval_id": "publication-eval::003::ai-reviewer-record::old",
            },
        }
    )
    writer_dispatch["prompt_contract"]["owner_route"] = writer_route
    writer_dispatch["prompt_contract"]["required_output_surface"] = writer_dispatch["required_output_surface"]
    writer_dispatch["prompt_contract"]["allowed_write_surfaces"] = [
        "paper/draft.md",
        "paper/build/review_manuscript.md",
        "paper/claim_evidence_map.json",
        "paper/evidence_ledger.json",
        "paper/review/**",
    ]
    writer_path = dispatch_dir / "run_quality_repair_batch.json"
    immutable_writer_path = dispatch_dir / "immutable" / "run_quality_repair_batch" / "dd76a2fe47b4c2bcc0771490.json"
    writer_dispatch["refs"] = {
        "dispatch_path": str(writer_path),
        "immutable_dispatch_path": str(immutable_writer_path),
        "stage_packet_path": str(immutable_writer_path),
    }
    _write_json(writer_path, writer_dispatch)
    _write_json(immutable_writer_path, writer_dispatch)
    _write_json(
        study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json",
        {
            "surface": "quality_repair_batch",
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "status": "handoff_ready",
            "next_owner": "write",
            "source_eval_id": "publication-eval::003::ai-reviewer-record::old",
            "writer_worker_handoff": writer_dispatch,
        },
    )
    _write_json(
        study_root / "paper" / "review" / "domain_stage_closeout_sat_story_delta_20260602T202258Z.json",
        {
            "surface_kind": "domain_stage_closeout_packet",
            "stage_id": "domain_owner/default-executor-dispatch",
            "study_id": study_id,
            "quest_id": f"quest-{study_id}",
            "action_type": "run_quality_repair_batch",
            "action_id": writer_dispatch["action_id"],
            "status": "completed_for_write_owner_delta",
            "route_outcome": "write_repair_delta_recorded",
            "source_eval_id": "publication-eval::003::ai-reviewer-record::old",
            "stage_packet_ref": (
                f"studies/{study_id}/artifacts/supervision/consumer/default_executor_dispatches/immutable/"
                "run_quality_repair_batch/dd76a2fe47b4c2bcc0771490.json"
            ),
            "artifact_delta": {
                "status": "materialized",
                "story_surface_delta_present": True,
                "manuscript_surface_hygiene": {
                    "status": "clear",
                    "story_surface_delta_required": True,
                    "story_surface_delta_present": True,
                },
                "changed_artifact_refs": [
                    {"path": str(study_root / "paper" / "draft.md")},
                    {"path": str(study_root / "paper" / "build" / "review_manuscript.md")},
                ],
            },
            "domain_owner_evidence": {
                "repair_execution_status": "materialized",
                "story_surface_delta_present": True,
                "manuscript_surface_hygiene_status": "clear",
            },
            "owner_receipt": {"status": "executed"},
        },
    )
    _write_json(
        profile.workspace_root / module.SUPERVISION_LATEST_RELATIVE_PATH,
        {
            "surface": "portable_owner_route_reconcile",
            "schema_version": 1,
            "studies": [
                {
                    "study_id": study_id,
                    "owner_route": ai_route,
                    "action_queue": [
                        {
                            "study_id": study_id,
                            "action_type": "return_to_ai_reviewer_workflow",
                            "owner_route": ai_route,
                        }
                    ],
                }
            ],
        },
    )
    _write_json(
        profile.workspace_root / "artifacts" / "supervision" / "consumer" / "latest.json",
        {
            "surface": "domain_action_request_materializer",
            "schema_version": 1,
            "default_executor_dispatches": [
                writer_dispatch,
            ],
        },
    )
    monkeypatch.setattr(
        module.action_execution.quality_repair.quality_repair_batch,
        "run_quality_repair_batch",
        lambda **_: {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
        },
    )

    result = module.dispatch_domain_owner_actions(
        profile=profile,
        study_ids=(study_id,),
        mode="developer_apply_safe",
        apply=True,
    )

    assert result["executions"] == []
    assert result["executed_count"] == 0
    assert result["blocked_count"] == 0
