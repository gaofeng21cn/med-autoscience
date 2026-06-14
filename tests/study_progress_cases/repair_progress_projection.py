from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_repair_progress_projection_carries_recheck_and_gate_done_flags(tmp_path: Path) -> None:
    repair_projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.repair_progress_projection"
    )
    study_root = tmp_path / "workspace" / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"
    paper_root = study_root / "paper"
    draft = paper_root / "draft.md"
    review = paper_root / "build" / "review_manuscript.md"
    for path in (draft, review):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("current\n", encoding="utf-8")
    evidence_path = study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    receipt_path = study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json"
    gate_request = study_root / "artifacts" / "controller" / "gate_replay_requests" / "latest.json"
    ai_request = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    _write_json(
        evidence_path,
        {
            "surface": "repair_execution_evidence",
            "status": "progress_delta_candidate",
            "progress_delta_candidate": True,
            "source_fingerprint": "repair-source-current",
            "repair_work_unit": {
                "unit_id": "medical_prose_write_repair",
                "source_eval_id": "eval-current",
            },
            "canonical_artifact_delta": {
                "meaningful_artifact_delta": True,
                "artifact_refs": [
                    {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
                    {"path": str(review), "artifact_role": "canonical_manuscript_story_surface"},
                ],
            },
            "gate_replay_done": True,
            "gate_replay_refs": [str(gate_request)],
            "ai_reviewer_recheck_required": True,
            "ai_reviewer_recheck_done": True,
            "ai_reviewer_recheck_request_ref": str(ai_request),
        },
    )
    _write_json(
        receipt_path,
        {
            "surface": "paper_story_repair_owner_receipt",
            "accepted": True,
            "work_unit_id": "medical_prose_write_repair",
            "execution_status": "progress_delta_candidate",
            "canonical_artifact_delta_refs": [
                {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
            ],
            "repair_execution_evidence_ref": str(evidence_path),
            "direct_current_package_write": False,
            "quality_authorized": False,
            "submission_authorized": False,
        },
    )

    repair_progress = repair_projection.build_repair_progress_projection(study_root=study_root)

    assert repair_progress["paper_delta_observed"] is True
    assert repair_progress["ai_reviewer_recheck_required"] is True
    assert repair_progress["ai_reviewer_recheck_done"] is True
    assert repair_progress["gate_replay_done"] is True
    assert repair_progress["gate_replay_refs"] == [str(gate_request)]


def test_repair_progress_projection_accepts_executed_quality_batch_owner_result(
    tmp_path: Path,
) -> None:
    repair_projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.repair_progress_projection"
    )
    study_root = tmp_path / "workspace" / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"
    paper_root = study_root / "paper"
    draft = paper_root / "draft.md"
    review = paper_root / "build" / "review_manuscript.md"
    for path in (draft, review):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("current\n", encoding="utf-8")
    evidence_path = study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    quality_batch_path = study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    gate_report = study_root / "runtime" / "quests" / "003-dpcc-primary-care-phenotype-treatment-gap" / "artifacts" / "reports" / "publishability_gate" / "2026-06-14T075221Z.json"
    gate_record = study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
    ai_request = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    _write_json(
        evidence_path,
        {
            "surface": "repair_execution_evidence",
            "status": "progress_delta_candidate",
            "progress_delta_candidate": True,
            "repair_work_unit": {"unit_id": "medical_prose_write_repair"},
            "review_finding": {"source_eval_id": "eval-current"},
            "source_fingerprint": "sha256:repair-evidence-current",
            "canonical_artifact_delta": {
                "status": "fresh",
                "meaningful_artifact_delta": True,
                "artifact_refs": [
                    {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
                    {"path": str(review), "artifact_role": "canonical_manuscript_story_surface"},
                ],
            },
            "changed_artifact_refs": [
                {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
            ],
            "gate_replay_done": True,
            "gate_replay_refs": [str(gate_report), str(gate_record)],
            "ai_reviewer_recheck_required": True,
            "ai_reviewer_recheck_done": True,
            "ai_reviewer_recheck_request_ref": str(ai_request),
            "quality_authorized": False,
            "submission_authorized": False,
            "current_package_write_authorized": False,
            "blockers": [],
        },
    )
    _write_json(
        quality_batch_path,
        {
            "schema_version": 1,
            "status": "executed",
            "ok": True,
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "source_eval_id": "eval-current",
            "repair_execution_evidence_path": str(evidence_path),
            "blocked_reason": None,
            "typed_blocker": None,
            "authority_route_gate": {
                "authorized": True,
                "allowed": True,
                "controller_route_gate": {
                    "authorized": True,
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                },
            },
        },
    )

    repair_progress = repair_projection.build_repair_progress_projection(study_root=study_root)

    assert repair_progress["paper_delta_observed"] is True
    assert repair_progress["accepted_owner_receipt"] is True
    assert repair_progress["owner_receipt_ref"] == str(quality_batch_path)
    assert repair_progress["work_unit_id"] == "medical_prose_write_repair"
    assert repair_progress["source_eval_id"] == "eval-current"
    assert repair_progress["changed_artifact_refs"] == [
        {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
        {"path": str(review), "artifact_role": "canonical_manuscript_story_surface"},
    ]


def test_repair_progress_projection_rejects_quality_batch_without_current_eval_identity(
    tmp_path: Path,
) -> None:
    repair_projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.repair_progress_projection"
    )
    study_root = tmp_path / "workspace" / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"
    draft = study_root / "paper" / "draft.md"
    draft.parent.mkdir(parents=True, exist_ok=True)
    draft.write_text("current\n", encoding="utf-8")
    evidence_path = study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    quality_batch_path = study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"
    _write_json(
        evidence_path,
        {
            "surface": "repair_execution_evidence",
            "status": "progress_delta_candidate",
            "progress_delta_candidate": True,
            "repair_work_unit": {"unit_id": "medical_prose_write_repair"},
            "canonical_artifact_delta": {
                "meaningful_artifact_delta": True,
                "artifact_refs": [
                    {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
                ],
            },
            "quality_authorized": False,
            "submission_authorized": False,
            "current_package_write_authorized": False,
            "blockers": [],
        },
    )
    _write_json(
        quality_batch_path,
        {
            "schema_version": 1,
            "status": "executed",
            "ok": True,
            "source_eval_id": "eval-current",
            "repair_execution_evidence_path": str(evidence_path),
            "blocked_reason": None,
            "typed_blocker": None,
            "authority_route_gate": {"authorized": True, "allowed": True},
        },
    )

    repair_progress = repair_projection.build_repair_progress_projection(study_root=study_root)

    assert repair_progress["paper_delta_observed"] is False
    assert repair_progress["accepted_owner_receipt"] is False
    assert repair_progress["owner_receipt_ref"] is None


def test_existing_progress_projection_refreshes_stable_repair_delta_over_old_stage_packet_blocker(
    tmp_path: Path,
) -> None:
    progress = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    quest_root = profile.runtime_root / study_id
    publication_eval_id = "publication-eval::dm002::current-after-owner-repair"
    draft = study_root / "paper" / "draft.md"
    claim_map = study_root / "paper" / "claim_evidence_map.json"
    evidence_ledger = study_root / "paper" / "evidence_ledger.json"
    review_ledger = study_root / "paper" / "review" / "review_ledger.json"
    for path, content in (
        (draft, "# Current draft\n\nClaim evidence has been repaired.\n"),
        (claim_map, '{"schema_version":1,"status":"current"}\n'),
        (evidence_ledger, '{"schema_version":1,"status":"current"}\n'),
        (review_ledger, '{"schema_version":1,"status":"current"}\n'),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "schema_version": 1,
            "eval_id": publication_eval_id,
            "study_id": study_id,
            "quest_id": study_id,
            "overall_verdict": "blocked",
        },
    )
    ai_request = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    gate_request = study_root / "artifacts" / "controller" / "gate_replay_requests" / "latest.json"
    evidence_path = study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    receipt_path = study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json"
    _write_json(
        ai_request,
        {
            "request_kind": "return_to_ai_reviewer_workflow",
            "request_owner": "ai_reviewer",
            "request_lifecycle": {"state": "requested"},
            "target_surface": "artifacts/publication_eval/latest.json",
        },
    )
    _write_json(
        gate_request,
        {
            "request_kind": "run_gate_replay_after_repair",
            "request_lifecycle": {"state": "requested"},
        },
    )
    _write_json(
        evidence_path,
        {
            "surface": "repair_execution_evidence",
            "status": "progress_delta_candidate",
            "progress_delta_candidate": True,
            "source_fingerprint": "repair-source-current",
            "repair_work_unit": {
                "unit_id": "analysis_claim_evidence_repair",
                "source_eval_id": publication_eval_id,
            },
            "canonical_artifact_delta": {
                "meaningful_artifact_delta": True,
                "artifact_refs": [
                    {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
                    {"path": str(claim_map), "artifact_role": "claim_evidence_map"},
                    {"path": str(evidence_ledger), "artifact_role": "evidence_ledger"},
                    {"path": str(review_ledger), "artifact_role": "review_ledger"},
                ],
            },
            "changed_artifact_refs": [
                {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
                {"path": str(claim_map), "artifact_role": "claim_evidence_map"},
            ],
            "gate_replay_done": True,
            "gate_replay_refs": [str(gate_request)],
            "ai_reviewer_recheck_required": True,
            "ai_reviewer_recheck_done": True,
            "ai_reviewer_recheck_request_ref": str(ai_request),
        },
    )
    _write_json(
        receipt_path,
        {
            "surface": "paper_story_repair_owner_receipt",
            "accepted": True,
            "work_unit_id": "analysis_claim_evidence_repair",
            "canonical_artifact_delta_refs": [
                {"path": str(draft), "artifact_role": "canonical_manuscript_story_surface"},
                {"path": str(claim_map), "artifact_role": "claim_evidence_map"},
            ],
            "repair_execution_evidence_ref": str(evidence_path),
            "ai_reviewer_recheck_request_ref": str(ai_request),
            "gate_replay_request_ref": str(gate_request),
            "direct_current_package_write": False,
            "quality_authorized": False,
            "submission_authorized": False,
        },
    )
    old_blocker = {
        "surface_kind": "current_work_unit",
        "schema_version": 1,
        "status": "typed_blocker",
        "study_id": study_id,
        "quest_id": study_id,
        "owner": "one-person-lab",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "analysis_claim_evidence_repair",
        "work_unit_fingerprint": "owner-route::write::manuscript_story_surface_delta_missing::run_quality_repair_batch",
        "state": {
            "state_kind": "typed_blocker",
            "typed_blocker": {
                "blocker_id": "stage_packet_not_current_selected_dispatch",
                "blocker_type": "stage_packet_not_current_selected_dispatch",
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "owner-route::write::manuscript_story_surface_delta_missing::run_quality_repair_batch",
            },
        },
    }
    status_payload = {
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": study_id,
        "study_root": str(study_root),
        "quest_root": str(quest_root),
        "decision": "blocked",
        "reason": "stage_packet_not_current_selected_dispatch",
        "active_run_id": None,
        "publication_eval": {
            "eval_id": publication_eval_id,
            "study_id": study_id,
            "quest_id": study_id,
        },
        "runtime_health_snapshot": {
            "runtime_health_epoch": "runtime-health-after-owner-repair",
            "worker_liveness_state": {"state": "ready", "worker_running": True},
        },
        "study_truth_snapshot": {
            "truth_epoch": "truth-event-after-owner-repair",
            "source_signature": "truth-source-after-owner-repair",
        },
        "progress_projection": {
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": study_id,
            "quest_root": str(quest_root),
            "current_stage": "queued",
            "paper_stage": "publishability_gate_blocked",
            "current_work_unit": old_blocker,
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "one-person-lab",
                "typed_blocker": old_blocker["state"]["typed_blocker"],
            },
            "current_executable_owner_action": None,
            "opl_current_control_state_handoff": {
                "typed_blocker": old_blocker["state"]["typed_blocker"],
                "blocked_reason": "stage_packet_not_current_selected_dispatch",
                "running_provider_attempt": False,
            },
            "progress_first_sprint_state": {"paper_progress_delta_counted": False},
            "refs": {"publication_eval_path": str(publication_eval_path)},
        },
    }

    result = progress.build_study_progress_projection(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        status_payload=status_payload,
        profile_ref=profile.profile_ref,
        materialize_read_model_artifacts=False,
    )

    repair_progress = result["repair_progress_projection"]
    assert repair_progress["paper_delta_observed"] is True
    assert result["paper_progress_delta"]["count"] == 1
    assert result["current_executable_owner_action"]["source"] == (
        "repair_progress_projection.mas_owner_repair_execution_evidence"
    )
    assert result["current_executable_owner_action"]["action_type"] == "run_gate_clearing_batch"
    assert result["current_work_unit"]["status"] == "executable_owner_action"
    assert result["current_work_unit"]["work_unit_id"] == "publication_gate_replay"
    assert result["paper_recovery_state"]["phase"] == "owner_action_ready"
