def test_study_runtime_status_preserves_current_ai_reviewer_publication_eval(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_runtime_router")
    decision_module = importlib.import_module("med_autoscience.controllers.study_runtime_decision")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.runtime_root / "001-risk"
    runtime_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    gate_report_path = quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
    write_text(quest_root / "quest.yaml", "quest_id: 001-risk\n")
    write_text(quest_root / ".ds" / "runtime_state.json", '{"status":"paused"}\n')
    charter_path = study_root / "artifacts" / "controller" / "study_charter.json"
    write_text(
        charter_path,
        json.dumps(
            {
                "schema_version": 1,
                "charter_id": "charter::001-risk::v1",
                "study_id": "001-risk",
                "publication_objective": "risk stratification external validation",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    write_text(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        json.dumps(
            {
                "schema_version": 1,
                "eval_id": "publication-eval::001-risk::001-risk::2026-04-17T02:10:00+00:00",
                "study_id": "001-risk",
                "quest_id": "001-risk",
                "emitted_at": "2026-04-17T02:10:00+00:00",
                "evaluation_scope": "publication",
                "charter_context_ref": {
                    "ref": str(charter_path),
                    "charter_id": "charter::001-risk::v1",
                    "publication_objective": "risk stratification external validation",
                },
                "runtime_context_refs": {
                    "runtime_escalation_ref": str(
                        quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"
                    ),
                    "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
                },
                "delivery_context_refs": {
                    "paper_root_ref": str(runtime_paper_root),
                    "submission_minimal_ref": str(runtime_paper_root / "submission_minimal" / "submission_manifest.json"),
                },
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "source_kind": "ai_reviewer_publication_assessment",
                    "policy_id": "medical_publication_critique_v1",
                    "source_refs": [str(runtime_paper_root / "review" / "review.md")],
                    "ai_reviewer_required": False,
                },
                "verdict": {
                    "overall_verdict": "mixed",
                    "primary_claim_status": "supported",
                    "summary": "AI reviewer closed the scientific quality loop.",
                    "stop_loss_pressure": "none",
                },
                "gaps": [
                    {
                        "gap_id": "gap-001",
                        "gap_type": "delivery",
                        "severity": "important",
                        "summary": "Author-side metadata remains.",
                        "evidence_refs": [str(gate_report_path)],
                    }
                ],
                "recommended_actions": [
                    {
                        "action_id": "action-ai-reviewer-finalize",
                        "action_type": "continue_same_line",
                        "priority": "now",
                        "reason": "Continue finalize handoff without reopening science.",
                        "route_target": "finalize",
                        "route_key_question": "Complete finalize handoff.",
                        "route_rationale": "AI reviewer closed the scientific loop.",
                        "evidence_refs": [str(runtime_paper_root / "review" / "review.md")],
                        "requires_controller_decision": True,
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )
    monkeypatch.setattr(
        module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": True,
            "runtime_contract": {"ready": True},
            "launcher_contract": {"ready": True},
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, "001-risk"),
    )
    monkeypatch.setattr(decision_module.publication_gate_controller, "build_gate_state", lambda quest_root: object())
    monkeypatch.setattr(
        decision_module.publication_gate_controller,
        "build_gate_report",
        lambda state: {
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-17T02:14:11+00:00",
            "quest_id": "001-risk",
            "paper_root": str(runtime_paper_root),
            "latest_gate_path": str(gate_report_path),
            "status": "blocked",
            "blockers": ["submission_surface_qc_failure_present"],
            "supervisor_phase": "bundle_stage_ready",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "continue_bundle_stage",
            "deferred_downstream_actions": [],
            "controller_stage_note": "bundle-stage work is unlocked",
        },
    )

    module.study_runtime_status(profile=profile, study_id="001-risk")

    payload = json.loads((study_root / "artifacts" / "publication_eval" / "latest.json").read_text(encoding="utf-8"))
    assert payload["assessment_provenance"]["owner"] == "ai_reviewer"
    assert payload["assessment_provenance"]["ai_reviewer_required"] is False
    assert payload["verdict"]["overall_verdict"] == "mixed"
    assert payload["emitted_at"] == "2026-04-17T02:10:00+00:00"
    assert payload["recommended_actions"][0]["reason"] == "Continue finalize handoff without reopening science."

__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
