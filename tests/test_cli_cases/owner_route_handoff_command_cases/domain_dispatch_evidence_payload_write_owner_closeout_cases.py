from __future__ import annotations

from .shared import *  # noqa: F403,F401


def test_domain_handler_dispatch_evidence_payload_projects_write_owner_domain_stage_closeout(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    stage_attempt_id = "sat_d7bfb1a5e2dcc40c0a9a7b55"
    stage_attempt_source = "mas_default_executor_source_48c11c88413fec90173057c3"
    domain_source = "6c182c42c32b60d7"
    dispatch_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
        "consumer/default_executor_dispatches/immutable/run_quality_repair_batch/"
        "37f378a74925d6be76360dfe.json"
    )
    closeout_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/paper/review/"
        f"domain_stage_closeout_{stage_attempt_id}_20260529T020700Z.json"
    )
    story_delta_ref = (
        "studies/003-dpcc-primary-care-phenotype-treatment-gap/paper/review/"
        f"manuscript_story_repair_story_surface_{stage_attempt_id}_20260529T020700Z.json"
    )
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        workspace_root / closeout_ref,
        {
            "surface_kind": "domain_stage_closeout_packet",
            "schema_version": 1,
            "stage_attempt_id": stage_attempt_id,
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_packet_ref": dispatch_ref,
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "owner": "write",
            "generated_at": "2026-05-29T02:07:00Z",
            "status": "completed_for_write_owner",
            "required_output_surface": "canonical manuscript story-surface delta",
            "typed_blocker": None,
            "domain_completion_claimed": False,
            "provider_completion_is_domain_completion": False,
            "provider_completion_is_domain_ready": False,
            "authority_boundary": {
                "provider_completion_is_domain_ready": False,
                "domain_ready_verdict": "not_asserted",
                "publication_quality_authorized": False,
                "submission_authorized": False,
                "paper_package_mutation_allowed": False,
                "quality_gate_relaxation_allowed": False,
                "manual_study_patch_allowed": False,
            },
            "verification": {
                "draft_review_manuscript_cmp": {
                    "observed_stdout": "cmp_exit=0",
                    "exit_code": 0,
                },
                "hash_and_size": {
                    "sha256": "8c42e4c368219a5cc1dd677bd75456a4292b497776ad92812845d747ee6055a8",
                    "byte_count_each_surface": 22968,
                },
            },
            "artifact_delta": {
                "status": "materialized",
                "artifact_refs": [
                    "paper/draft.md",
                    "paper/build/review_manuscript.md",
                    story_delta_ref,
                ],
                "previous_controller_fingerprint_sha256": (
                    "bd3071079f9d7ec97517ce30d70f79240a0d60582634b40b7ed34a2d9611f153"
                ),
                "new_fingerprint_sha256": (
                    "8c42e4c368219a5cc1dd677bd75456a4292b497776ad92812845d747ee6055a8"
                ),
            },
            "closeout_refs": [
                closeout_ref,
                story_delta_ref,
                "studies/003-dpcc-primary-care-phenotype-treatment-gap/paper/draft.md",
                "studies/003-dpcc-primary-care-phenotype-treatment-gap/paper/build/review_manuscript.md",
                dispatch_ref,
            ],
        },
    )
    _write_json(
        workspace_root / story_delta_ref,
        {
            "schema_version": 1,
            "surface": "manuscript_story_repair_story_surface_stage_packet",
            "stage_attempt_id": stage_attempt_id,
            "stage_id": "domain_owner/default-executor-dispatch",
            "stage_packet_ref": dispatch_ref,
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "story_surface_delta": {
                "status": "present",
                "delta_type": "medical_prose_and_story_surface_reconciliation",
            },
            "route_outcome": "write_owner_story_surface_delta_materialized",
        },
    )
    workorder_path = tmp_path / "opl-workorder.json"
    _write_json(
        workorder_path,
        {
            "action_id": f"domain_dispatch:medautoscience:{stage_attempt_id}:record",
            "target_identity": {
                "domain_id": "medautoscience",
                "stage_id": "domain_owner/default-executor-dispatch",
                "stage_attempt_id": stage_attempt_id,
                "task_kind": "domain_owner/default-executor-dispatch",
                "study_id": study_id,
                "source_fingerprint": stage_attempt_source,
                "domain_source_fingerprint": domain_source,
                "profile_name": "dm-cvd-mortality-risk",
            },
            "dispatch_identity_fields": {
                "action_type": "run_quality_repair_batch",
                "dispatch_ref": dispatch_ref,
            },
        },
    )

    def fake_scan_domain_routes(*, profile, study_ids, apply_safe_actions, developer_supervisor_mode):
        return {
            "studies": [
                {
                    "study_id": study_id,
                    "blocked_reason": "paper_authority_clean_migration_required",
                    "domain_transition": {
                        "decision_type": "ai_reviewer_re_eval",
                        "route_target": "review",
                        "owner": "ai_reviewer",
                        "controller_action": "return_to_ai_reviewer_workflow",
                        "completion_receipt_consumption": {
                            "status": "consumed",
                            "receipt_kind": "ai_reviewer_publication_eval",
                            "next_action": "honor_ai_reviewer_publication_eval_authority",
                        },
                    },
                    "owner_route": {
                        "next_owner": "external_supervisor",
                        "owner_reason": "paper_authority_clean_migration_required",
                    },
                }
            ]
        }

    monkeypatch.setattr(cli.owner_route_reconcile, "scan_domain_routes", fake_scan_domain_routes)

    exit_code = cli.main(
        [
            "domain-handler",
            "dispatch-evidence-payload",
            "--profile",
            str(profile_path),
            "--workorder",
            str(workorder_path),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["status"] == "owner_receipt_payload_ready"
    assert payload["payload_reason"] == (
        "stage_attempt_closeout_owner_receipt_observed_for_default_executor_dispatch"
    )
    evidence_payload = payload["domain_dispatch_evidence_record_payload"]
    assert evidence_payload["mode"] == "refs_only_domain_owned_success_payload"
    record_payload = payload["opl_runtime_action_execute_payload"]
    assert record_payload["source_fingerprint"] == stage_attempt_source
    assert record_payload["domain_source_fingerprint"] == domain_source
    assert record_payload["typed_blocker_refs"] == []
    assert record_payload["domain_owner_receipt_refs"] == [f"{closeout_ref}#write_owner_closeout"]
    assert closeout_ref in record_payload["evidence_refs"]
    assert story_delta_ref in record_payload["evidence_refs"]
    assert dispatch_ref in record_payload["evidence_refs"]
    assert "stage-attempt-closeout:status=completed_for_write_owner" in record_payload["evidence_refs"]
    assert "stage-attempt-closeout:owner=write" in record_payload["evidence_refs"]
    assert "stage-attempt-closeout:artifact_delta_status=materialized" in record_payload["evidence_refs"]
    assert record_payload["no_regression_refs"]
    assert evidence_payload["domain_ready_claimed"] is False
    assert evidence_payload["publication_ready_claimed"] is False
    assert evidence_payload["artifact_mutation_authorized"] is False
