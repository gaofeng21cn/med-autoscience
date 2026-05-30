from __future__ import annotations

from .shared import *  # noqa: F403,F401


def test_domain_handler_stage_evidence_payload_projects_review_quality_gate_typed_blocker(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workorder_path = tmp_path / "opl-stage-workorder.json"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    _write_json(
        workorder_path,
        {
            "surface_kind": "opl_stage_production_evidence_payload_workorder",
            "request_id": "stage_production_evidence:medautoscience:review_and_quality_gate",
            "request_pack_id": "medautoscience.stage_production_evidence",
            "action_id": "stage-production-evidence:medautoscience:review_and_quality_gate:record",
            "target_domain_id": "med-autoscience",
            "command_domain_id": "medautoscience",
            "stage_id": "review_and_quality_gate",
            "success_path_requires": {
                "domain_receipt_refs_cover": [],
                "domain_receipt_instance_required_for_declared_refs": [
                    "owner_receipt:review_and_quality_gate"
                ],
                "evidence_refs_cover_monitor_freshness": [
                    "/progress_projection",
                    "/product_entry_manifest/family_stage_control_plane/stages/"
                    "review_and_quality_gate/freshness",
                ],
                "source_scope_refs_cover": [
                    "review",
                    "decision",
                    "/product_entry_manifest/family_stage_control_plane/stages/"
                    "review_and_quality_gate/source_refs",
                ],
                "runtime_event_refs_cover": [
                    "runtime_event:ai_reviewer_publication_eval.gate_receipt_recorded",
                    "runtime_event:publication_eval.ai_reviewer_gate_receipt_recorded",
                ],
            },
        },
    )

    exit_code = cli.main(
        [
            "domain-handler",
            "stage-evidence-payload",
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
    assert payload["surface_kind"] == "mas_stage_production_evidence_payload_export"
    assert payload["status"] == "typed_blocker_payload_ready"
    assert payload["stage_id"] == "review_and_quality_gate"
    assert payload["payload_reason"] == (
        "stage_production_evidence_typed_blocker_pending_real_owner_receipt_or_monitor_freshness"
    )
    assert payload["stage_expected_receipt_refs"] == ["owner_receipt:review_and_quality_gate"]
    assert payload["stage_monitor_freshness_refs"] == [
        "/progress_projection",
        "/product_entry_manifest/family_stage_control_plane/stages/"
        "review_and_quality_gate/freshness",
    ]
    assert payload["stage_source_scope_refs"] == [
        "review",
        "decision",
        "/product_entry_manifest/family_stage_control_plane/stages/"
        "review_and_quality_gate/source_refs",
    ]
    assert payload["stage_runtime_event_refs"] == [
        "runtime_event:ai_reviewer_publication_eval.gate_receipt_recorded",
        "runtime_event:publication_eval.ai_reviewer_gate_receipt_recorded",
    ]

    action_payload = payload["opl_runtime_action_execute_payload"]
    assert action_payload["research_evidence_pack_ref"] == (
        "mas-research-evidence-pack:medautoscience:stage_production_evidence:"
        "review_and_quality_gate"
    )
    assert action_payload["research_evidence_pack_summary"] == {
        "surface_kind": "mas_research_evidence_pack_summary",
        "version": "mas-research-evidence-pack-summary.v1",
        "domain_id": "medautoscience",
        "study_id": None,
        "stage_id": "review_and_quality_gate",
        "task_kind": "stage_production_evidence",
        "pack_ref": (
            "mas-research-evidence-pack:medautoscience:stage_production_evidence:"
            "review_and_quality_gate"
        ),
        "run_manifest_ref": (
            "mas-research-run-manifest:medautoscience:stage_production_evidence:"
            "review_and_quality_gate"
        ),
        "negative_failed_path_ledger_ref": (
            "mas-negative-failed-path-ledger:medautoscience:stage_production_evidence:"
            "review_and_quality_gate"
        ),
        "decision_trace_ref": (
            "mas-decision-trace:medautoscience:stage_production_evidence:"
            "review_and_quality_gate"
        ),
        "artifact_lineage_graph_ref": (
            "mas-artifact-lineage-graph:medautoscience:stage_production_evidence:"
            "review_and_quality_gate"
        ),
        "reproducibility_bundle_ref": (
            "mas-reproducibility-bundle:medautoscience:stage_production_evidence:"
            "review_and_quality_gate"
        ),
        "claim_impact_refs": [],
        "code_refs": [],
        "decision_trace_refs": [],
        "negative_failed_path_refs": [],
        "source_data_version_refs": [],
        "software_environment_refs": [],
        "parameter_seed_refs": [],
        "input_refs": [
            "stage_production_evidence:medautoscience:review_and_quality_gate",
            "medautoscience.stage_production_evidence",
            "stage-production-evidence:medautoscience:review_and_quality_gate:record",
            "/progress_projection",
            "/product_entry_manifest/family_stage_control_plane/stages/"
            "review_and_quality_gate/freshness",
            "review",
            "decision",
            "/product_entry_manifest/family_stage_control_plane/stages/"
            "review_and_quality_gate/source_refs",
            "runtime_event:ai_reviewer_publication_eval.gate_receipt_recorded",
            "runtime_event:publication_eval.ai_reviewer_gate_receipt_recorded",
            "contracts/production_acceptance/mas-production-acceptance.json"
            "#/paper_line_guarded_apply_evidence",
        ],
        "output_refs": [],
        "checksum_refs": [
            "mas-no-forbidden-write-proof:medautoscience:"
            "stage-production-evidence:review_and_quality_gate:refs-only-payload"
        ],
        "typed_blocker_refs": [
            "mas-stage-typed-blocker:medautoscience:review_and_quality_gate:"
            "real-paper-line-owner-receipt-or-monitor-freshness-pending"
        ],
        "owner_receipt_refs": [],
        "progress_summary": {
            "surface_kind": "mas_research_pack_progress_summary",
            "body_included": False,
            "paper_body_included": False,
            "deliverable_progress_delta": {"count": 0, "refs": []},
            "paper_progress_delta": {"count": 0, "refs": []},
            "platform_repair_delta": {
                "count": 0,
                "refs": [],
                "counts_as_paper_progress": False,
            },
            "negative_result_count": 0,
            "negative_failed_path_refs": [],
            "route_switch_count": 0,
            "route_switch_refs": [],
            "missing_reproducibility_refs": [
                "code_refs",
                "source_data_version_refs",
                "software_environment_refs",
                "parameter_seed_refs",
            ],
            "single_next_owner_blocker": {
                "status": "blocked",
                "ref": (
                    "mas-stage-typed-blocker:medautoscience:review_and_quality_gate:"
                    "real-paper-line-owner-receipt-or-monitor-freshness-pending"
                ),
                "candidate_count": 1,
                "body_included": False,
                "is_route_authority": False,
            },
            "authority_boundary": {
                "summary_only": True,
                "body_free": True,
                "is_route_authority": False,
                "can_authorize_route_switch": False,
                "can_authorize_artifact_mutation": False,
                "can_authorize_publication_readiness": False,
                "platform_repair_counts_as_paper_progress": False,
            },
        },
        "authority_boundary": {
            "owner": "med-autoscience",
            "opl_records_refs_only": True,
            "can_read_domain_body": False,
            "can_accept_or_reject_owner_receipt": False,
            "can_sign_domain_receipt": False,
            "can_authorize_artifact_mutation": False,
            "can_authorize_publication_readiness": False,
            "domain_ready_claimed": False,
        },
    }
    assert action_payload["domain_receipt_refs"] == []
    assert action_payload["evidence_refs"] == []
    assert action_payload["source_scope_refs"] == []
    assert action_payload["runtime_event_refs"] == []
    assert action_payload["typed_blocker_refs"] == [
        "mas-stage-typed-blocker:medautoscience:review_and_quality_gate:"
        "real-paper-line-owner-receipt-or-monitor-freshness-pending"
    ]
    assert action_payload["no_regression_refs"] == [
        "mas-no-forbidden-write-proof:medautoscience:"
        "stage-production-evidence:review_and_quality_gate:refs-only-payload"
    ]

    record_payload = payload["domain_dispatch_evidence_record_payload"]
    assert record_payload["surface_kind"] == "mas_domain_dispatch_evidence_record_payload"
    assert record_payload["task_kind"] == "stage_production_evidence"
    assert record_payload["stage_id"] == "review_and_quality_gate"
    assert record_payload["body_included"] is False
    assert record_payload["domain_ready_claimed"] is False
    assert record_payload["publication_ready_claimed"] is False
    assert record_payload["artifact_mutation_authorized"] is False
    assert record_payload["record_payload"]["stage_expected_receipt_refs"] == payload[
        "stage_expected_receipt_refs"
    ]
    assert record_payload["record_payload"]["stage_monitor_freshness_refs"] == payload[
        "stage_monitor_freshness_refs"
    ]
    assert record_payload["record_payload"]["stage_runtime_event_refs"] == payload[
        "stage_runtime_event_refs"
    ]
    assert record_payload["stage_evidence_handoff"]["identity_binding"] == record_payload[
        "identity_binding"
    ]
    assert payload["authority_boundary"]["opl_records_refs_only"] is True
    assert payload["authority_boundary"]["creates_owner_receipt"] is False
    assert payload["authority_boundary"]["claims_stage_ready"] is False
    assert payload["authority_boundary"]["exports_research_evidence_pack_refs_only"] is True


def test_domain_handler_stage_evidence_payload_projects_review_quality_gate_success_refs(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    workorder_path = tmp_path / "opl-stage-workorder.json"
    study_root = workspace_root / "studies" / "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "assessment_provenance": {"owner": "ai_reviewer"},
            "eval_id": "publication-eval-dm002",
            "reviewer_operating_system": {"trace_id": "ai-reviewer-os-dm002"},
        },
    )
    _write_json(
        workorder_path,
        {
            "surface_kind": "opl_stage_production_evidence_payload_workorder",
            "request_id": "stage_production_evidence:medautoscience:review_and_quality_gate",
            "request_pack_id": "medautoscience.stage_production_evidence",
            "action_id": "stage-production-evidence:medautoscience:review_and_quality_gate:record",
            "target_domain_id": "med-autoscience",
            "command_domain_id": "medautoscience",
            "stage_id": "review_and_quality_gate",
            "success_path_requires": {
                "domain_receipt_refs_cover": [],
                "domain_receipt_instance_required_for_declared_refs": [
                    "owner_receipt:review_and_quality_gate"
                ],
                "evidence_refs_cover_monitor_freshness": [
                    "/progress_projection",
                    "/product_entry_manifest/family_stage_control_plane/stages/"
                    "review_and_quality_gate/freshness",
                ],
                "source_scope_refs_cover": [
                    "review",
                    "decision",
                    "/product_entry_manifest/family_stage_control_plane/stages/"
                    "review_and_quality_gate/source_refs",
                ],
                "runtime_event_refs_cover": [
                    "runtime_event:ai_reviewer_publication_eval.gate_receipt_recorded",
                    "runtime_event:publication_eval.ai_reviewer_gate_receipt_recorded",
                ],
            },
        },
    )

    exit_code = cli.main(
        [
            "domain-handler",
            "stage-evidence-payload",
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
    assert payload["status"] == "success_payload_ready"
    assert payload["payload_reason"] == "stage_production_evidence_review_quality_gate_refs_observed"
    action_payload = payload["opl_runtime_action_execute_payload"]
    assert action_payload["research_evidence_pack_ref"] == (
        "mas-research-evidence-pack:medautoscience:stage_production_evidence:"
        "review_and_quality_gate"
    )
    assert action_payload["research_evidence_pack_summary"]["owner_receipt_refs"] == [
        str(study_root / "artifacts" / "publication_eval" / "latest.json")
    ]
    assert action_payload["research_evidence_pack_summary"]["typed_blocker_refs"] == []
    assert action_payload["research_evidence_pack_summary"]["output_refs"] == [
        str(study_root / "artifacts" / "publication_eval" / "latest.json")
    ]
    assert action_payload["domain_receipt_refs"] == [
        str(study_root / "artifacts" / "publication_eval" / "latest.json")
    ]
    assert action_payload["evidence_refs"] == payload["stage_monitor_freshness_refs"]
    assert action_payload["source_scope_refs"] == payload["stage_source_scope_refs"]
    assert action_payload["runtime_event_refs"] == payload["stage_runtime_event_refs"]
    assert action_payload["typed_blocker_refs"] == []
    assert action_payload["no_regression_refs"] == [
        "mas-no-forbidden-write-proof:medautoscience:"
        "stage-production-evidence:review_and_quality_gate:refs-only-payload"
    ]
    record_payload = payload["domain_dispatch_evidence_record_payload"]
    assert record_payload["mode"] == "refs_only_domain_owned_success_payload"
    assert record_payload["record_payload"]["stage_expected_receipt_refs"] == action_payload[
        "domain_receipt_refs"
    ]
    assert record_payload["record_payload"]["stage_monitor_freshness_refs"] == action_payload[
        "evidence_refs"
    ]
    assert record_payload["record_payload"]["stage_runtime_event_refs"] == action_payload[
        "runtime_event_refs"
    ]
    assert record_payload["domain_ready_claimed"] is False
    assert record_payload["publication_ready_claimed"] is False
    assert record_payload["artifact_mutation_authorized"] is False
    assert payload["authority_boundary"]["creates_owner_receipt"] is False
    assert payload["authority_boundary"]["claims_stage_ready"] is False


def test_domain_handler_stage_evidence_payload_fails_closed_for_wrong_domain(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workorder_path = tmp_path / "opl-stage-workorder.json"
    write_profile(profile_path, workspace_root=tmp_path / "workspace")
    _write_json(
        workorder_path,
        {
            "request_id": "stage_production_evidence:redcube:review_and_revision",
            "request_pack_id": "redcube.stage_production_evidence",
            "action_id": "stage-production-evidence:redcube:review_and_revision:record",
            "command_domain_id": "redcube",
            "stage_id": "review_and_revision",
        },
    )

    exit_code = cli.main(
        [
            "domain-handler",
            "stage-evidence-payload",
            "--profile",
            str(profile_path),
            "--workorder",
            str(workorder_path),
            "--format",
            "json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["status"] == "blocked"
    assert payload["blocked_reason"] == "workorder_domain_not_medautoscience"
