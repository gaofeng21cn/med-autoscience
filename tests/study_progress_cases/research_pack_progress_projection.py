from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_research_pack_progress_summary_projects_from_current_control_state(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff_projection",
            "schema_version": 1,
            "generated_at": "2026-05-04T06:00:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "running",
                    "active_run_id": "run-001",
                    "runtime_health": {"health_status": "escalated"},
                    "blocked_reason": "runtime_recovery_retry_budget_exhausted",
                    "latest_terminal_stage_log": {
                        "surface_kind": "mas_latest_terminal_stage_log_projection",
                        "read_model": "study_latest_terminal_stage_log_projection",
                        "authority": "observability_only",
                        "study_id": "001-risk",
                        "paper_stage_log": {
                            "surface_kind": "mas_paper_facing_stage_log_summary",
                            "stage_name": "write",
                            "research_evidence_pack_summary": {
                                "surface_kind": "mas_research_evidence_pack_summary",
                                "schema_validation": {
                                    "status": "fail_closed_missing_required_refs",
                                    "missing_required_evidence_families": [
                                        "reproducibility_refs"
                                    ],
                                    "fail_closed_reasons": ["missing_required_refs"],
                                    "placeholder_ref_families": [],
                                    "forbidden_write_refs": [],
                                    "owner_route_mismatch_refs": [],
                                    "body_free_payload": True,
                                    "non_body_free_payload_detected": False,
                                    "ref_family_status": {
                                        "run_manifest_ref": {
                                            "status": "present",
                                            "ref_count": 1,
                                            "refs": ["run-manifest-ref:001-risk"],
                                            "body_included": False,
                                        },
                                        "negative_failed_path_refs": {
                                            "status": "present",
                                            "ref_count": 2,
                                            "refs": [
                                                "negative-ledger-ref:a",
                                                "negative-ledger-ref:b",
                                            ],
                                            "body_included": False,
                                        },
                                        "decision_trace_refs": {
                                            "status": "present",
                                            "ref_count": 1,
                                            "refs": ["decision-trace-ref:001-risk"],
                                            "body_included": False,
                                        },
                                        "artifact_lineage_refs": {
                                            "status": "present",
                                            "ref_count": 1,
                                            "refs": ["artifact-lineage-ref:001-risk"],
                                            "body_included": False,
                                        },
                                        "reproducibility_refs": {
                                            "status": "blocker",
                                            "ref_count": 0,
                                            "refs": [],
                                            "body_included": False,
                                        },
                                        "owner_receipt_or_typed_blocker_refs": {
                                            "status": "blocker",
                                            "ref_count": 1,
                                            "refs": [
                                                "studies/001-risk/artifacts/blockers/next-owner.json"
                                            ],
                                            "body_included": False,
                                        },
                                    },
                                },
                                "progress_summary": {
                                    "surface_kind": "mas_research_pack_progress_summary",
                                    "body_included": False,
                                    "paper_body_included": False,
                                    "deliverable_progress_delta": {
                                        "count": 1,
                                        "refs": ["studies/001-risk/paper/draft.md"],
                                    },
                                    "paper_progress_delta": {
                                        "count": 1,
                                        "refs": ["studies/001-risk/paper/draft.md"],
                                    },
                                    "platform_repair_delta": {
                                        "count": 1,
                                        "refs": [
                                            "studies/001-risk/artifacts/controller/currentness/latest.json"
                                        ],
                                        "counts_as_paper_progress": False,
                                    },
                                    "negative_result_count": 2,
                                    "route_switch_count": 1,
                                    "missing_reproducibility_refs": ["parameter_seed_refs"],
                                    "single_next_owner_blocker": {
                                        "status": "blocked",
                                        "ref": "studies/001-risk/artifacts/blockers/next-owner.json",
                                        "candidate_count": 1,
                                        "body_included": False,
                                        "is_route_authority": False,
                                    },
                                    "evidence_tail_closure_summary": {
                                        "surface_kind": "mas_paper_line_evidence_tail_closure_summary",
                                        "study_id": "001-risk",
                                        "all_required_tails_closed": False,
                                        "summary_counts": {
                                            "required_tail_count": 5,
                                            "closed_tail_count": 4,
                                            "evidence_gap_count": 0,
                                            "stable_blocker_count": 1,
                                            "not_triggered_count": 1,
                                        },
                                        "tails": {
                                            "real_paper_line_provider_apply": {
                                                "status": "refs_observed",
                                                "refs": ["owner-receipt-ref:001-risk"],
                                                "required": True,
                                                "body_included": False,
                                            },
                                            "publication_route_memory_writeback": {
                                                "status": "refs_observed",
                                                "refs": ["memory-writeback-ref:001-risk"],
                                                "required": True,
                                                "body_included": False,
                                            },
                                            "artifact_lifecycle": {
                                                "status": "closed_by_stable_typed_blocker",
                                                "refs": [
                                                    "studies/001-risk/artifacts/blockers/next-owner.json"
                                                ],
                                                "required": True,
                                                "body_included": False,
                                            },
                                            "human_gate_resume": {
                                                "status": "not_triggered",
                                                "refs": [],
                                                "required": True,
                                                "body_included": False,
                                            },
                                            "family_transition_live_receipt": {
                                                "status": "refs_observed",
                                                "refs": ["stage-expected-ref:001-risk"],
                                                "required": True,
                                                "body_included": False,
                                            },
                                        },
                                    },
                                },
                            },
                        },
                    },
                }
            ],
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "decision": "blocked",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "runtime_health_snapshot": {"attempt_state": "escalated"},
            "authority_snapshot": {"control_state": "blocked_runtime_escalation"},
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["refs"]["opl_current_control_state_handoff_path"] == str(handoff_path)
    research_pack_summary = result["research_pack_progress_summary"]
    assert research_pack_summary["body_included"] is False
    assert research_pack_summary["paper_body_included"] is False
    assert research_pack_summary["deliverable_progress_delta"]["count"] == 1
    assert research_pack_summary["paper_progress_delta"]["count"] == 1
    assert research_pack_summary["platform_repair_delta"] == {
        "count": 1,
        "refs": ["studies/001-risk/artifacts/controller/currentness/latest.json"],
        "counts_as_paper_progress": False,
    }
    assert research_pack_summary["negative_result_count"] == 2
    assert research_pack_summary["route_switch_count"] == 1
    assert research_pack_summary["missing_reproducibility_refs"] == ["parameter_seed_refs"]
    assert research_pack_summary["single_next_owner_blocker"]["ref"] == (
        "studies/001-risk/artifacts/blockers/next-owner.json"
    )
    assert research_pack_summary["evidence_tail_closure_summary"]["summary_counts"] == {
        "required_tail_count": 5,
        "closed_tail_count": 4,
        "evidence_gap_count": 0,
        "stable_blocker_count": 1,
        "not_triggered_count": 1,
    }
    assert research_pack_summary["evidence_tail_closure_summary"]["tails"][
        "artifact_lifecycle"
    ]["status"] == "closed_by_stable_typed_blocker"
    assert research_pack_summary["evidence_tail_closure_summary"]["authority"]["is_route_authority"] is False
    assert research_pack_summary["single_next_owner_blocker"]["is_route_authority"] is False
    assert research_pack_summary["schema_validation"] == {
        "status": "fail_closed_missing_required_refs",
        "missing_required_evidence_families": ["reproducibility_refs"],
        "fail_closed_reasons": ["missing_required_refs"],
        "placeholder_ref_families": [],
        "forbidden_write_refs": [],
        "owner_route_mismatch_refs": [],
        "body_free_payload": True,
        "non_body_free_payload_detected": False,
        "body_included": False,
    }
    assert research_pack_summary["ref_family_status"]["reproducibility_refs"] == {
        "status": "blocker",
        "ref_count": 0,
        "refs": [],
        "body_included": False,
    }
    assert research_pack_summary["ref_family_status"]["owner_receipt_or_typed_blocker_refs"]["status"] == (
        "blocker"
    )
    assert research_pack_summary["authority"]["is_route_authority"] is False
    assert research_pack_summary["authority"]["platform_repair_counts_as_paper_progress"] is False
