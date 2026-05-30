from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_progress_freshness_does_not_treat_control_surface_as_artifact_delta(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-dm",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    _write_publication_eval(study_root, quest_root)
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {
            "recorded_at": "2026-05-09T07:05:46+00:00",
            "health_status": "live",
            "summary": "runtime heartbeat only",
        },
    )
    _write_json(
        study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {
            "surface": "autonomy_progress_slo_status",
            "schema_version": 1,
            "study_id": "002-dm",
            "quest_id": "quest-002",
            "state": "breach",
            "breach_types": ["same_fingerprint_loop"],
            "last_meaningful_progress_at": "2026-05-09T07:05:46+00:00",
            "last_meaningful_progress": {
                "last_meaningful_progress_at": "2026-05-09T07:05:46+00:00",
                "source": "mas_control_surface",
                "source_ref": None,
            },
            "mds_progress_markers": {
                "meaningful_artifact_delta_at": None,
                "meaningful_artifact_delta_kind": None,
                "turn_progress_kind": None,
            },
            "ai_doctor_request_required": True,
            "ai_doctor_state": "request_ready",
            "quality_gate_relaxation_allowed": False,
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "002-dm",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-002", "auto_resume": True},
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_liveness_status": "live",
            "active_run_id": "run-live-control-only",
            "worker_running": True,
                "runtime_liveness_audit": {
                    "status": "live",
                    "active_run_id": "run-live-control-only",
                    "runtime_audit": {
                        "status": "live",
                        "active_run_id": "run-live-control-only",
                        "worker_running": True,
                        "worker_watchdog": {"started_at": "2026-05-09T07:05:46+00:00"},
                    },
                },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
                "latest_recorded_at": "2026-05-09T07:05:46+00:00",
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 5, 9, 7, 5, 55, tzinfo=timezone.utc),
    )

    result = module.read_study_progress(profile=profile, study_id="002-dm")

    assert result["last_meaningful_progress_at"] == "2026-05-09T07:05:46+00:00"
    assert result["progress_freshness"]["supervisor_tick_freshness"]["status"] == "fresh"
    artifact_freshness = result["progress_freshness"]["meaningful_artifact_delta_freshness"]
    assert artifact_freshness["status"] == "missing"
    assert artifact_freshness["latest_progress_at"] is None
    assert artifact_freshness["latest_progress_source"] == "mds_artifact_delta"
    assert result["progress_freshness"]["activity_timeout"]["state"] == "watching_new_run"
    assert result["user_visible_projection"]["actual_write_active"] is False


def test_study_progress_counts_gate_clearing_paper_outputs_as_artifact_delta(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-dm",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    eval_id = "publication-eval::002-dm::quest-002::2026-05-09T08:00:00+00:00"
    _write_publication_eval(study_root, quest_root)
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    publication_eval = json.loads(publication_eval_path.read_text(encoding="utf-8"))
    publication_eval["eval_id"] = eval_id
    publication_eval_path.write_text(json.dumps(publication_eval, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _write_json(
        study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json",
        {
            "schema_version": 1,
            "source_eval_id": eval_id,
            "status": "executed",
            "unit_results": [
                {
                    "unit_id": "repair_paper_live_paths",
                    "status": "updated",
                    "result": {
                        "status": "updated",
                        "repaired_files": [
                            str(study_root / "paper" / "claim_evidence_map.json"),
                            str(study_root / "paper" / "evidence_ledger.json"),
                        ],
                    },
                },
                {
                    "unit_id": "materialize_display_surface",
                    "status": "materialized",
                    "result": {
                        "status": "materialized",
                        "written_files": [
                            str(study_root / "paper" / "figures" / "generated" / "F1_cohort_flow.png"),
                            str(study_root / "paper" / "tables" / "generated" / "T1_baseline.md"),
                        ],
                    },
                },
                {
                    "unit_id": "create_submission_minimal_package",
                    "status": "authority_route_blocked",
                    "result": {
                        "status": "authority_route_blocked",
                        "paper_root": str(study_root / "paper"),
                    },
                },
            ],
            "gate_replay": {"status": "blocked", "blockers": ["claim_evidence_consistency_failed"]},
            "gate_replay_step": {
                "step_id": "publication_gate_replay",
                "status": "blocked",
                "finished_at": "2026-05-09T08:10:00+00:00",
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {
            "surface": "autonomy_progress_slo_status",
            "schema_version": 1,
            "study_id": "002-dm",
            "quest_id": "quest-002",
            "state": "breach",
            "breach_types": ["same_fingerprint_loop"],
            "last_meaningful_progress_at": "2026-05-09T07:05:46+00:00",
            "mds_progress_markers": {
                "meaningful_artifact_delta_at": None,
                "meaningful_artifact_delta_kind": None,
                "turn_progress_kind": None,
            },
            "ai_doctor_request_required": True,
            "ai_doctor_state": "request_ready",
            "quality_gate_relaxation_allowed": False,
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "002-dm",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-002", "auto_resume": True},
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_liveness_status": "live",
            "active_run_id": "run-live-gate-artifact",
            "worker_running": True,
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-live-gate-artifact",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-live-gate-artifact",
                    "worker_running": True,
                    "worker_watchdog": {"started_at": "2026-05-09T08:00:00+00:00"},
                },
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
                "latest_recorded_at": "2026-05-09T08:11:00+00:00",
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 5, 9, 8, 12, tzinfo=timezone.utc),
    )

    result = module.read_study_progress(profile=profile, study_id="002-dm")

    artifact_freshness = result["progress_freshness"]["meaningful_artifact_delta_freshness"]
    assert artifact_freshness["status"] == "fresh"
    assert artifact_freshness["latest_progress_at"] == "2026-05-09T08:10:00+00:00"
    assert artifact_freshness["latest_progress_source"] == "gate_clearing_batch"
    assert "4 paper-facing artifact(s)" in artifact_freshness["summary"]
    assert set(artifact_freshness["changed_refs"]) == {
        str(study_root / "paper" / "claim_evidence_map.json"),
        str(study_root / "paper" / "evidence_ledger.json"),
        str(study_root / "paper" / "figures" / "generated" / "F1_cohort_flow.png"),
        str(study_root / "paper" / "tables" / "generated" / "T1_baseline.md"),
    }
    assert result["progress_freshness"]["activity_timeout"]["state"] == "ok"
    assert result["user_visible_projection"]["actual_write_active"] is True
    assert result["user_visible_projection"]["paper_progress_state"]["state"] == "progressing"
    assert result["user_visible_projection"]["paper_progress_state"]["paper_facing_progress_slo"]["visible_as_progressing"] is True
    assert "系统有实际 writer/run 正在推进" in result["user_visible_projection"]["status_summary"]


def test_study_progress_counts_runtime_closeout_paper_outputs_as_artifact_delta(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dm",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-003"
    _write_publication_eval(study_root, quest_root)
    _write_json(
        quest_root / "artifacts" / "runtime" / "turn_closeouts" / "run-paper-delta.json",
        {
            "schema_version": 1,
            "status": "completed",
            "completed_at": "2026-05-13T14:55:14Z",
            "meaningful_artifact_delta": True,
            "artifact_refs": [
                "../../../studies/003-dm/paper/claim_evidence_map.json",
                "../../../studies/003-dm/paper/evidence_ledger.json",
                "../../../studies/003-dm/paper/review/review_ledger.json",
                "artifacts/reports/publishability_gate/latest.json",
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {
            "surface": "autonomy_progress_slo_status",
            "schema_version": 1,
            "study_id": "003-dm",
            "quest_id": "quest-003",
            "state": "breach",
            "breach_types": ["same_fingerprint_loop"],
            "last_meaningful_progress_at": "2026-05-13T14:50:00+00:00",
            "mds_progress_markers": {
                "meaningful_artifact_delta_at": None,
                "meaningful_artifact_delta_kind": None,
                "turn_progress_kind": None,
            },
            "ai_doctor_request_required": True,
            "ai_doctor_state": "request_ready",
            "quality_gate_relaxation_allowed": False,
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "003-dm",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-003", "auto_resume": True},
            "quest_id": "quest-003",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_liveness_status": "live",
            "active_run_id": "run-live-after-closeout",
            "worker_running": True,
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-live-after-closeout",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-live-after-closeout",
                    "worker_running": True,
                    "worker_watchdog": {"started_at": "2026-05-13T14:57:00+00:00"},
                },
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
                "latest_recorded_at": "2026-05-13T14:57:00+00:00",
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 5, 13, 15, 0, tzinfo=timezone.utc),
    )

    result = module.read_study_progress(profile=profile, study_id="003-dm")

    artifact_freshness = result["progress_freshness"]["meaningful_artifact_delta_freshness"]
    assert artifact_freshness["status"] == "fresh"
    assert artifact_freshness["latest_progress_at"] == "2026-05-13T14:55:14+00:00"
    assert artifact_freshness["latest_progress_source"] == "runtime_turn_closeout"
    assert "3 paper-facing artifact(s)" in artifact_freshness["summary"]
    assert artifact_freshness["changed_refs"] == [
        "../../../studies/003-dm/paper/claim_evidence_map.json",
        "../../../studies/003-dm/paper/evidence_ledger.json",
        "../../../studies/003-dm/paper/review/review_ledger.json",
    ]
    assert result["progress_freshness"]["activity_timeout"]["state"] == "ok"
    assert result["user_visible_projection"]["actual_write_active"] is True
    assert result["user_visible_projection"]["paper_progress_state"]["state"] == "progressing"
    assert result["user_visible_projection"]["paper_progress_state"]["paper_facing_progress_slo"]["visible_as_progressing"] is True
