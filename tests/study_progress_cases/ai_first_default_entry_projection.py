from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_progress_projects_ai_first_default_entry_state_fail_closed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "assessment_provenance": {
                "owner": "mechanical_projection",
                "source_kind": "publication_gate_report",
                "policy_id": "publication_gate_projection_v1",
                "ai_reviewer_required": True,
            },
            "verdict": {
                "overall_verdict": "mixed",
                "summary": "Mechanical projection cannot authorize quality closure.",
            },
            "recommended_actions": [],
        },
    )
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
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")
    markdown = module.render_study_progress_markdown(result)

    state = result["ai_first_default_entry_state"]
    assert state["surface"] == "ai_first_default_entry_state"
    assert state["status"] == "review_required"
    assert state["pre_draft"]["draft_ready"] is False
    assert state["pre_draft"]["route_back_required"] is True
    assert state["pre_draft"]["authoring_workplan_projection"] == {
        "surface": "authoring_workplan_projection",
        "exists": False,
        "status": "",
        "workplan_ready": False,
        "required_before": "first_full_draft",
        "source_family": "",
        "section_count": 0,
        "work_unit_count": 0,
        "blockers": ["authoring_workplan_missing"],
        "authority": {
            "read_only": True,
            "can_authorize_draft_readiness": False,
            "can_mutate_runtime": False,
        },
    }
    assert state["ai_reviewer_workflow"]["authority_state"] == "projection_only"
    assert state["ai_reviewer_workflow"]["finalize_authorized"] is False
    assert state["ai_reviewer_workflow"]["submission_authorized"] is False
    assert state["artifact_proof"]["rebuild_pending"] is True
    assert state["human_review_required"] is True
    assert state["authority"]["default_entry_can_authorize_quality"] is False
    assert result["ai_first_operations_dashboard"]["user_view"]["human_review_required"] is True
    assert "AI-first 默认入口状态" in markdown
    assert "Pre-draft readiness" in markdown
    assert "AI reviewer workflow" in markdown
    assert "Artifact proof" in markdown
    feedback = result["ai_first_feedback_state"]
    assert feedback["surface"] == "ai_first_feedback_state"
    assert feedback["authority"] == "observability_only"
    assert feedback["status"] == "attention_required"
    assert feedback["counts"]["ai_reviewer_trace_incomplete_count"] == 1
    assert feedback["counts"]["artifact_rebuild_pending_count"] == 1
    assert feedback["authority_contract"]["feedback_can_authorize_submission"] is False
    assert feedback["primary_action"]["action_id"] == "return_to_ai_reviewer_workflow"
    assert feedback["user_view"]["next_action"] == "补齐 AI reviewer workflow、publication eval 与 medical prose review。"
    assert result["refs"]["ai_first_feedback_ledger_path"].endswith(
        "artifacts/runtime/ai_first_feedback_ledger/latest.json"
    )
    assert result["refs"]["ai_first_action_dispatch_ledger_path"].endswith(
        "artifacts/runtime/ai_first_action_dispatch_ledger/latest.json"
    )
    action_dispatch = result["ai_first_action_dispatch_ledger"]
    assert action_dispatch["surface"] == "ai_first_action_dispatch_ledger"
    assert action_dispatch["authority"] == "operations_governance_only"
    assert action_dispatch["counts"]["open"] >= 1
    assert action_dispatch["counts"]["total"] == len(action_dispatch["dispatches"])
    assert {
        item["dispatch_key"]
        for item in action_dispatch["dispatches"]
    } == {
        item["dispatch_key"]
        for item in module.ai_first_action_dispatch.read_action_dispatch_ledger(study_root=study_root)["dispatches"]
    }
    lifecycle = result["ai_first_action_lifecycle"]
    assert lifecycle["surface"] == "ai_first_action_lifecycle_projection"
    assert lifecycle["primary_action"]["action_id"] == "return_to_ai_reviewer_workflow"
    assert lifecycle["open_action_count"] == action_dispatch["counts"]["open"]
    assert lifecycle["authority_contract"]["lifecycle_can_authorize_quality"] is False
    assert lifecycle["authority_contract"]["lifecycle_can_authorize_submission"] is False
    second = module.read_study_progress(profile=profile, study_id="001-risk")
    first_keys = {item["dispatch_key"] for item in action_dispatch["dispatches"]}
    second_keys = {
        item["dispatch_key"]
        for item in second["ai_first_action_dispatch_ledger"]["dispatches"]
    }
    assert first_keys.issubset(second_keys)
    assert len(second_keys) == second["ai_first_action_dispatch_ledger"]["counts"]["total"]
    assert "AI-first 运行反馈" in markdown
    assert "建议动作: 补齐 AI reviewer workflow、publication eval 与 medical prose review。" in markdown


def test_study_progress_projects_ai_first_action_dispatch_lifecycle(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    dispatch = importlib.import_module("med_autoscience.controllers.ai_first_action_dispatch")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    _write_json(
        study_root / "artifacts" / "runtime" / "ai_first_action_dispatch_ledger" / "latest.json",
        {
            "surface": "ai_first_action_dispatch_ledger",
            "schema_version": 1,
            "authority": "operations_governance_only",
            "dispatches": [
                {
                    "dispatch_key": "feedback::return_to_ai_reviewer_workflow::ai_reviewer_runtime_workflow",
                    "action_id": "return_to_ai_reviewer_workflow",
                    "target_surface": "ai_reviewer_runtime_workflow",
                    "source_feedback_key": "ai_reviewer_trace_gap",
                    "summary": "补齐 AI reviewer workflow、publication eval 与 medical prose review。",
                    "status": "in_progress",
                    "prompt": "internal prompt must stay hidden",
                    "token_count": 1234,
                }
            ],
            "counts": {"in_progress": 1, "total": 1},
        },
    )
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
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")
    markdown = module.render_study_progress_markdown(result)

    lifecycle = result["ai_first_action_dispatch_lifecycle"]
    assert lifecycle["surface"] == "ai_first_action_dispatch_lifecycle"
    assert lifecycle["primary_action"]["status"] == "in_progress"
    assert lifecycle["primary_action"]["action_id"] == "return_to_ai_reviewer_workflow"
    assert lifecycle["counts"]["in_progress"] >= 1
    assert lifecycle["counts"]["active"] >= 1
    assert result["refs"]["ai_first_action_dispatch_ledger_path"] == str(
        dispatch.stable_action_dispatch_ledger_path(study_root=study_root)
    )
    assert "AI-first 动作生命周期" in markdown
    assert "主动作状态: in_progress" in markdown
    assert "补齐 AI reviewer workflow、publication eval 与 medical prose review。" in markdown
    assert "internal prompt" not in markdown
    assert "token_count" not in markdown


def test_study_progress_projects_paper_orchestra_operator_read_model_without_new_runtime_truth(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    _write_json(
        study_root / "paper" / "authoring_workplan.json",
        {
            "schema_version": 1,
            "surface": "authoring_workplan",
            "status": "in_progress",
            "sections": [
                {
                    "section_id": "introduction",
                    "section_title": "Introduction",
                    "status": "ready",
                    "owner": "medical_writer",
                    "parallelizable": True,
                    "task_refs": ["write_clinical_problem"],
                },
                {
                    "section_id": "methods",
                    "section_title": "Methods",
                    "status": "ready",
                    "owner": "methods_writer",
                    "parallelizable": True,
                    "task_refs": ["write_population", "write_analysis_plan"],
                },
                {
                    "section_id": "discussion",
                    "section_title": "Discussion",
                    "status": "waiting",
                    "owner": "ai_reviewer",
                    "depends_on": ["results"],
                    "blockers": ["results_section_not_ready"],
                },
            ],
            "work_units": [
                {
                    "work_unit_id": "write_clinical_problem",
                    "status": "ready",
                    "owner": "medical_writer",
                    "section_id": "introduction",
                },
                {
                    "work_unit_id": "write_population",
                    "status": "ready",
                    "owner": "methods_writer",
                    "section_id": "methods",
                },
                {
                    "work_unit_id": "write_analysis_plan",
                    "status": "ready",
                    "owner": "methods_writer",
                    "section_id": "methods",
                },
            ],
            "authority": {
                "source_family": "PaperOrchestra-inspired",
                "read_model_only": True,
                "can_authorize_draft_readiness": False,
            },
        },
    )
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
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")
    markdown = module.render_study_progress_markdown(result)

    projection = result["paper_orchestra_operator_projection"]
    assert projection["surface"] == "paper_orchestra_operator_projection"
    assert projection["read_model"] == "paper_orchestra_operator_projection_read_model"
    assert projection["status"] == "blocked"
    assert projection["current_dag_stage"]["stage_id"] == "pre_draft_quality_gate"
    assert projection["current_dag_stage"]["owner"] == "MAS Quality OS"
    assert [item["section_id"] for item in projection["parallel_sections"]] == [
        "introduction",
        "methods",
    ]
    assert projection["parallel_section_count"] == 2
    gate_ids = [item["gate_id"] for item in projection["blocking_gates"]]
    assert gate_ids[:3] == [
        "pre_draft_quality_gate",
        "ai_reviewer_quality_gate",
        "artifact_rebuild_gate",
    ]
    assert "authoring_stage_graph:outline" in gate_ids
    assert "section_authoring_work_units" in gate_ids
    assert "medical_literature_hygiene_projection" in gate_ids
    assert "reviewer_refinement_loop" in gate_ids
    assert projection["next_owner"] == {
        "owner": "MAS Quality OS",
        "surface": "pre_draft_quality_runtime_state",
        "action": "close_pre_draft_quality_gate",
    }
    assert projection["pending_integration_surfaces"] == []
    assert projection["integrated_surfaces"]["authoring_stage_graph"]["surface"] == "authoring_stage_graph"
    assert projection["integrated_surfaces"]["section_authoring_work_units"]["surface"] == "section_authoring_work_units"
    assert (
        projection["integrated_surfaces"]["medical_literature_hygiene_projection"]["surface"]
        == "medical_literature_hygiene_projection"
    )
    assert projection["integrated_surfaces"]["reviewer_refinement_loop"]["surface"] == "reviewer_refinement_loop"
    assert projection["integrated_surfaces"]["quality_regression_projection"]["role"] == "calibration_evidence_only"
    assert projection["authority"] == {
        "read_only": True,
        "creates_runtime_truth": False,
        "can_mutate_runtime": False,
        "can_authorize_quality": False,
        "can_authorize_publication_ready": False,
        "can_authorize_submission": False,
        "mechanical_projection_can_authorize_quality": False,
    }
    assert result["ai_first_default_entry_state"]["paper_orchestra_operator_projection"] == projection
    assert "论文写作 DAG" in markdown
    assert "当前卡点: pre-draft quality gate" in markdown
    assert "可并行 section: introduction, methods" in markdown
    assert "下一责任方: MAS Quality OS" in markdown


def test_study_progress_operator_projection_integrates_landed_paper_orchestra_surfaces(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    paper_root = study_root / "paper"
    _write_json(
        paper_root / "authoring_workplan.json",
        {
            "schema_version": 1,
            "surface": "authoring_workplan",
            "status": "in_progress",
            "sections": [
                {
                    "section_id": "introduction",
                    "section_title": "Introduction",
                    "status": "ready",
                    "owner": "medical_writer",
                    "parallelizable": True,
                    "task_refs": ["write_clinical_problem"],
                },
                {
                    "section_id": "methods",
                    "section_title": "Methods",
                    "status": "ready",
                    "owner": "methods_writer",
                    "parallelizable": True,
                    "task_refs": ["write_population", "write_analysis_plan"],
                },
                {
                    "section_id": "discussion",
                    "section_title": "Discussion",
                    "status": "waiting",
                    "owner": "ai_reviewer",
                    "depends_on": ["results"],
                    "blockers": ["results_section_not_ready"],
                },
            ],
            "work_units": [
                {
                    "work_unit_id": "write_clinical_problem",
                    "status": "ready",
                    "owner": "medical_writer",
                    "section_id": "introduction",
                },
                {
                    "work_unit_id": "write_population",
                    "status": "ready",
                    "owner": "methods_writer",
                    "section_id": "methods",
                },
                {
                    "work_unit_id": "write_analysis_plan",
                    "status": "ready",
                    "owner": "methods_writer",
                    "section_id": "methods",
                },
            ],
            "authority": {
                "source_family": "PaperOrchestra-inspired",
                "read_model_only": True,
                "can_authorize_draft_readiness": False,
            },
        },
    )
    _write_json(
        paper_root / "pre_draft_writing_readiness.json",
        {
            "schema_version": 1,
            "surface": "pre_draft_writing_readiness",
            "status": "closed",
            "readiness_items": [
                {
                    "readiness_id": readiness_id,
                    "status": "closed",
                    "evidence_refs": ["paper/medical_manuscript_blueprint.json"],
                }
                for readiness_id in (
                    "clinical_question",
                    "population_design_outcome",
                    "display_to_claim_map",
                    "claim_evidence_map",
                    "section_purpose",
                    "reader_flow_plan",
                    "journal_voice",
                    "ai_prose_review_feedback_loop",
                )
            ],
        },
    )
    _write_json(
        paper_root / "medical_manuscript_blueprint.json",
        {
            "schema_version": 1,
            "surface": "medical_manuscript_blueprint",
            "status": "closed",
            "canonical_ready": True,
            "authoring_provenance": {
                "owner": "ai_author",
                "source_kind": "medical_manuscript_blueprint",
                "ai_reviewer_required": False,
            },
        },
    )
    _write_json(
        paper_root / "evidence_ledger.json",
        {
            "schema_version": 1,
            "surface": "evidence_ledger",
            "status": "closed",
            "items": [
                {
                    "citation_key": "pmid_12345",
                    "source_kind": "pubmed",
                    "pmid": "12345",
                    "doi": "10.1000/example",
                }
            ],
        },
    )
    _write_json(
        paper_root / "review_ledger.json",
        {
            "schema_version": 1,
            "surface": "review_ledger",
            "status": "closed",
            "closures": [{"closure_id": "review::core", "status": "closed"}],
        },
    )
    (paper_root / "references.bib").write_text(
        "@article{pmid_12345,title={Example},pmid={12345},doi={10.1000/example}}\n",
        encoding="utf-8",
    )
    (paper_root / "build").mkdir(parents=True)
    (paper_root / "build" / "review_manuscript.md").write_text(
        "The manuscript cites supported evidence [@pmid_12345].\n",
        encoding="utf-8",
    )
    manuscript_path = paper_root / "manuscript.md"
    manuscript_path.write_text("# Manuscript\n\nThe manuscript cites supported evidence [@pmid_12345].\n", encoding="utf-8")
    (paper_root / "evidence_ledger.md").write_text(
        "# Evidence ledger\n\n- primary-result-evidence: grounded.\n",
        encoding="utf-8",
    )
    _write_json(
        paper_root / "claim_evidence_map.json",
        {"claims": [{"claim_id": "primary-result", "status": "supported"}]},
    )
    _write_json(
        paper_root / "methods_implementation_manifest.json",
        {"study_design": {"cohort_definition": "Defined cohort."}},
    )
    _write_json(
        paper_root / "results_narrative_map.json",
        {"sections": [{"section_id": "results", "direct_answer": "Grounded result."}]},
    )
    _write_json(
        paper_root / "figure_semantics_manifest.json",
        {"figures": [{"figure_id": "Figure1", "direct_message": "Grounded display."}]},
    )
    _write_json(
        paper_root / "derived_analysis_manifest.json",
        {"numeric_results": [{"result_id": "primary_metric"}]},
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "medical_prose_review.json",
        {
            "schema_version": 1,
            "surface": "medical_prose_review",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "medical_prose_review",
                "policy_id": "medical_publication_critique_v1",
                "ai_reviewer_required": False,
            },
            "medical_journal_prose_quality": {
                "status": "ready",
                "overall_style_verdict": "clear",
                "summary": "Medical journal prose is clear.",
                "route_back_recommendation": {
                    "required": False,
                    "route_target": "none",
                    "reason": "No route back required.",
                },
            },
            "mechanical_safety_flags": [],
            "source_refs": [str(manuscript_path)],
        },
    )
    package_source_root = paper_root / "submission_minimal"
    package_source_root.mkdir(parents=True)
    (package_source_root / "manuscript.md").write_text(manuscript_path.read_text(encoding="utf-8"), encoding="utf-8")
    (package_source_root / "submission_manifest.json").write_text('{"status":"ready"}\n', encoding="utf-8")
    import hashlib

    signature_payload = []
    for relative in ("manuscript.md", "submission_manifest.json"):
        source = package_source_root / relative
        signature_payload.append(
            {
                "path": relative,
                "size": source.stat().st_size,
                "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            }
        )
    import json

    source_signature = hashlib.sha256(
        json.dumps(signature_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    _write_json(
        study_root / "manuscript" / "delivery_manifest.json",
        {
            "schema_version": 1,
            "stage": "submission_minimal",
            "source_signature": source_signature,
            "evaluated_source_signature": source_signature,
            "authority_source_signature": source_signature,
            "source_relative_paths": ["manuscript.md", "submission_manifest.json"],
            "source": {
                "paper_root": str(paper_root.resolve()),
                "package_source_root": str(package_source_root.resolve()),
            },
            "surface_roles": {
                "controller_authorized_paper_root": str(paper_root.resolve()),
                "controller_authorized_package_source_root": str(package_source_root.resolve()),
                "human_facing_current_package_root": str((study_root / "manuscript" / "current_package").resolve()),
                "human_facing_current_package_zip": str((study_root / "manuscript" / "current_package.zip").resolve()),
            },
            "blocking_artifact_refs": [],
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": "publication-eval::001-risk::quest-001::2026-05-03T00:00:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-05-03T00:00:00+00:00",
            "evaluation_scope": "publication",
            "charter_context_ref": {
                "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                "charter_id": "charter::001-risk::v1",
                "publication_objective": "Submit a manuscript-safe clinical paper.",
            },
            "runtime_context_refs": {
                "runtime_escalation_ref": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
            },
            "delivery_context_refs": {
                "paper_root_ref": str(paper_root),
                "submission_minimal_ref": str(package_source_root / "submission_manifest.json"),
            },
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
                "policy_id": "medical_publication_critique_v1",
                "source_refs": [str(paper_root)],
                "ai_reviewer_required": False,
            },
            "verdict": {
                "overall_verdict": "promising",
                "primary_claim_status": "supported",
                "summary": "AI reviewer accepts the current line.",
                "stop_loss_pressure": "none",
            },
            "quality_assessment": {
                "clinical_significance": {
                    "status": "ready",
                    "summary": "Clinical framing is ready.",
                    "evidence_refs": [str(paper_root / "medical_manuscript_blueprint.json")],
                },
                "evidence_strength": {
                    "status": "ready",
                    "summary": "Evidence strength is ready.",
                    "evidence_refs": [str(paper_root / "evidence_ledger.json")],
                },
                "novelty_positioning": {
                    "status": "ready",
                    "summary": "Novelty boundary is ready.",
                    "evidence_refs": [str(paper_root / "medical_manuscript_blueprint.json")],
                },
                "medical_journal_prose_quality": {
                    "status": "ready",
                    "summary": "Medical prose is ready.",
                    "evidence_refs": [str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json")],
                },
                "human_review_readiness": {
                    "status": "ready",
                    "summary": "Human review package is ready.",
                    "evidence_refs": [str(package_source_root / "submission_manifest.json")],
                },
            },
            "reviewer_operating_system": {
                "contract_id": "medical_publication_ai_reviewer_os_v1",
                "input_bundle": {
                    "manuscript": str(manuscript_path),
                    "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
                    "evidence_ledger": str(paper_root / "evidence_ledger.json"),
                    "review_ledger": str(paper_root / "review_ledger.json"),
                    "medical_manuscript_blueprint": str(paper_root / "medical_manuscript_blueprint.json"),
                    "claim_evidence_map": str(paper_root / "claim_evidence_map.json"),
                    "medical_prose_review": str(
                        study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
                    ),
                    "publication_gate_projection": str(
                        study_root / "artifacts" / "publication_eval" / "latest.json"
                    ),
                },
                "rubric_scores": {
                    dimension: {
                        "status": "ready",
                        "rationale": "Reviewer-backed surface.",
                        "evidence_refs": [str(manuscript_path)],
                    }
                    for dimension in (
                        "clinical_significance",
                        "evidence_strength",
                        "novelty_positioning",
                        "medical_journal_prose_quality",
                        "human_review_readiness",
                    )
                },
                "decision_matrix": [
                    {"dimension": "medical_journal_prose_quality", "status": "ready", "rationale": "ready"}
                ],
                "provenance_checks": {
                    "assessment_owner": "ai_reviewer",
                    "policy_id": "medical_publication_critique_v1",
                    "ai_reviewer_required": False,
                    "mechanical_projection_used_as_quality_authority": False,
                },
                "route_back_decision": {
                    "recommended_action": "accept_current_line",
                    "rationale": "No blocking reviewer refinement remains.",
                },
            },
            "gaps": [],
            "recommended_actions": [
                {
                    "action_id": "accept-current-line",
                    "action_type": "continue_same_line",
                    "priority": "next",
                    "reason": "Accepted current line.",
                    "route_target": "finalize",
                    "route_key_question": "Complete final author-facing handoff.",
                    "route_rationale": "Reviewer accepted the manuscript quality gate.",
                    "evidence_refs": [str(manuscript_path)],
                    "requires_controller_decision": True,
                }
            ],
        },
    )
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
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")
    markdown = module.render_study_progress_markdown(result)

    projection = result["paper_orchestra_operator_projection"]
    assert projection["status"] == "blocked"
    assert projection["current_dag_stage"]["stage_id"] in {
        "pre_draft_quality_gate",
        "reviewer_refinement_loop",
    }
    assert [item["section_id"] for item in projection["parallel_sections"]] == [
        "introduction",
        "methods",
        "results",
        "discussion",
    ]
    assert projection["pending_integration_surfaces"] == []
    integrated = projection["integrated_surfaces"]
    assert integrated["authoring_stage_graph"]["status"] == "blocked"
    assert "outline" in integrated["authoring_stage_graph"]["blocking_stage_ids"]
    assert integrated["section_authoring_work_units"]["status"] == "ready"
    assert integrated["medical_literature_hygiene_projection"]["status"] == "clear"
    assert integrated["reviewer_refinement_loop"]["accept_status"] == "blocked"
    assert integrated["quality_regression_projection"]["role"] == "calibration_evidence_only"
    assert integrated["quality_regression_projection"]["authority"]["can_authorize_publication_quality"] is False
    assert projection["authority"]["can_authorize_publication_ready"] is False
    assert result["ai_first_default_entry_state"]["paper_orchestra_operator_projection"] == projection
    assert "论文写作 DAG" in markdown
    assert "可并行 section: introduction, methods, results, discussion" in markdown
    assert "下一责任方:" in markdown
