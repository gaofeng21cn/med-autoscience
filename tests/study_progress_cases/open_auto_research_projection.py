from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def _write_open_auto_research_surfaces(study_root: Path) -> None:
    _write_json(
        study_root / "artifacts" / "medical_paper" / "literature_intelligence_os.json",
        {
            "surface": "literature_intelligence_os",
            "schema_version": 1,
            "study_id": "001-risk",
            "status": "ready",
            "missing_reason": "",
            "source_coverage": {
                "searched_source_count": 3,
                "anchor_paper_count": 2,
                "guideline_count": 1,
                "systematic_review_count": 1,
                "journal_neighbor_ref_count": 1,
                "citation_ledger_ref_count": 1,
                "evidence_node_count": 2,
                "perspective_question_count": 1,
                "contradiction_flag_count": 1,
            },
            "authority": {"can_authorize_publication_quality": False},
        },
    )
    _write_json(
        study_root / "artifacts" / "eval_hygiene" / "quality_regression_projection" / "latest.json",
        {
            "surface": "quality_regression_projection",
            "schema_version": 1,
            "authority": {
                "owner": "MAS Evaluation OS",
                "can_authorize_publication_quality": False,
            },
            "calibration_evidence": {
                "rubric_tree": {
                    "surface": "paperbench_style_hierarchical_rubric_tree",
                    "role": "calibration_evidence_only",
                    "can_authorize_publication_quality": False,
                    "can_authorize_submission_readiness": False,
                    "nodes": [{"node_id": "root", "children": [{"node_id": "root.evidence"}]}],
                }
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "action_observation_trajectory" / "latest.json",
        {
            "surface": "action_observation_trajectory",
            "schema_version": 1,
            "active_run_id": "run-001",
            "trajectory_role": {
                "read_model_only": True,
                "can_be_study_truth_owner": False,
                "can_be_publication_quality_owner": False,
            },
            "steps": [{"step_id": "step-001", "status": "observed"}],
            "replay_summary": {
                "auto_replayable_step_count": 1,
                "non_replayable_step_count": 0,
                "blocked_replay_reasons": [],
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "medical_paper" / "route_decision_orchestrator.json",
        {
            "surface": "route_decision_orchestrator",
            "status": "ready",
            "controller_decision_ref": str(
                study_root / "artifacts" / "controller_decisions" / "latest.json"
            ),
            "candidate_path_graph": {
                "surface": "candidate_path_graph",
                "authority": "read_model_only",
                "decision": "proceed",
                "selected_candidate_id": "line-b",
                "controller_decision_ref": str(
                    study_root / "artifacts" / "controller_decisions" / "latest.json"
                ),
                "candidates": [
                    {
                        "candidate_id": "line-b",
                        "question": "Can line-b answer the locked question?",
                        "evidence_basis": ["pmid:12345678"],
                        "expected_artifact": "artifacts/medical_paper/candidate_paths/line-b.json",
                        "stop_rule": "stop if transportability cannot be evaluated",
                        "decision": "proceed",
                        "controller_decision_ref": str(
                            study_root / "artifacts" / "controller_decisions" / "latest.json"
                        ),
                    }
                ],
            },
        },
    )


def test_study_progress_projects_open_auto_research_capabilities_without_authority_takeover(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    _write_open_auto_research_surfaces(study_root)

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "active_run_id": "run-001",
            "publication_supervisor_state": {
                "supervisor_phase": "write",
                "phase_owner": "publication_gate",
                "current_required_action": "continue_write_stage",
            },
            "supervisor_tick_audit": {"required": False, "status": "not_required"},
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")
    projection = result["open_auto_research_projection"]
    projection_path = (
        study_root / "artifacts" / "runtime" / "open_auto_research_projection" / "latest.json"
    )

    assert projection["surface"] == "open_auto_research_projection"
    assert projection["status"] == "ready"
    assert projection["counts"] == {
        "ready": 4,
        "blocked": 0,
        "needs_review": 0,
        "total": 4,
    }
    assert projection["capabilities"]["literature_evidence_graph"]["status"] == "ready"
    assert projection["capabilities"]["evaluation_rubric_tree"]["status"] == "ready"
    assert projection["capabilities"]["runtime_trajectory_proof"]["status"] == "ready"
    assert projection["capabilities"]["candidate_path_graph"]["status"] == "ready"
    assert projection["capabilities"]["evaluation_rubric_tree"]["role"] == "calibration_evidence_only"
    assert projection["actions"] == [
        {
            "action_id": "run_literature_evidence_graph",
            "status": "ready",
            "surface": "literature_intelligence_os",
        },
        {
            "action_id": "review_rubric_gaps",
            "status": "ready",
            "surface": "paperbench_style_hierarchical_rubric_tree",
        },
        {
            "action_id": "inspect_trajectory",
            "status": "ready",
            "surface": "action_observation_trajectory",
        },
        {
            "action_id": "refine_candidate_path",
            "status": "ready",
            "surface": "candidate_path_graph",
        },
    ]
    assert projection["authority"] == {
        "read_only": True,
        "can_mutate_runtime": False,
        "can_materialize_artifacts": False,
        "can_authorize_publication_quality": False,
        "can_authorize_submission": False,
        "can_replace_controller_decision": False,
        "can_replace_study_truth": False,
    }
    assert result["refs"]["open_auto_research_projection_path"].endswith(
        "artifacts/runtime/open_auto_research_projection/latest.json"
    )
    assert not projection_path.exists()
