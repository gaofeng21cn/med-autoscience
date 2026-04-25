from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_run_controller_refreshes_stale_journal_package_when_source_submission_manifest_advances(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    journal_package_module = importlib.import_module("med_autoscience.controllers.journal_package")
    requirements_module = importlib.import_module("med_autoscience.journal_requirements")
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
    )
    study_root = tmp_path / "studies" / "002-early-residual-risk"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    journal_slug = "rheumatology-international"

    dump_json(
        paper_root / "submission_targets.resolved.json",
        {
            "schema_version": 1,
            "updated_at": "2026-04-06T00:00:00+00:00",
            "decision_kind": "journal_selected",
            "decision_source": "controller_explicit",
            "primary_target": {
                "journal_name": "Rheumatology International",
                "journal_slug": journal_slug,
                "publication_profile": "general_medical_journal",
                "official_guidelines_url": "https://example.org/ri-guide",
                "package_required": True,
                "resolution_status": "resolved",
            },
            "blocked_items": [],
        },
    )
    requirements_module.write_journal_requirements(
        study_root=study_root,
        requirements=requirements_module.JournalRequirements(
            journal_name="Rheumatology International",
            journal_slug=journal_slug,
            official_guidelines_url="https://example.org/ri-guide",
            publication_profile="general_medical_journal",
            abstract_word_cap=250,
            title_word_cap=None,
            keyword_limit=None,
            main_text_word_cap=None,
            main_display_budget=6,
            table_budget=2,
            figure_budget=4,
            supplementary_allowed=True,
            title_page_required=True,
            blinded_main_document=False,
            reference_style_family="AMA",
            required_sections=(),
            declaration_requirements=(),
            submission_checklist_items=(),
            template_assets=(),
        ),
    )
    journal_package_module.materialize_journal_package(
        paper_root=paper_root,
        study_root=study_root,
        journal_slug=journal_slug,
        publication_profile="general_medical_journal",
    )
    source_manifest_path = paper_root / "submission_minimal" / "submission_manifest.json"
    source_manifest_payload = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    source_manifest_payload["generated_at"] = "2026-04-06T00:00:01+00:00"
    source_manifest_path.write_text(
        json.dumps(source_manifest_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(module.study_delivery_sync, "can_sync_study_delivery", lambda *, paper_root: True)
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_draft_handoff_delivery",
        lambda *, paper_root: {
            "applicable": False,
            "status": "not_applicable",
            "current_package_root": None,
            "current_package_zip": None,
            "delivery_manifest_path": None,
        },
    )
    monkeypatch.setattr(
        module.study_delivery_sync,
        "describe_submission_delivery",
        lambda *, paper_root, publication_profile="general_medical_journal": {
            "applicable": True,
            "status": "current",
            "stale_reason": None,
            "delivery_manifest_path": "/tmp/studies/002/manuscript/delivery_manifest.json",
            "current_package_root": "/tmp/studies/002/manuscript/current_package",
            "current_package_zip": "/tmp/studies/002/manuscript/current_package.zip",
            "missing_source_paths": [],
        },
    )

    result = module.run_controller(quest_root=quest_root, apply=True)

    assert result["status"] == "clear"
    assert result["allow_write"] is True
    assert result["current_required_action"] == "continue_bundle_stage"
    assert result["journal_package_sync"] == {
        "status": "materialized",
        "study_root": str(study_root.resolve()),
        "paper_root": str(paper_root.resolve()),
        "journal_slug": journal_slug,
        "journal_name": "Rheumatology International",
        "publication_profile": "general_medical_journal",
        "package_root": str((study_root / "submission_packages" / journal_slug).resolve()),
        "submission_manifest_path": str((study_root / "submission_packages" / journal_slug / "submission_manifest.json").resolve()),
        "zip_path": str((study_root / "submission_packages" / journal_slug / f"{journal_slug}_submission_package.zip").resolve()),
        "package_status": "current",
    }
def test_build_gate_report_blocks_unmanaged_submission_surface_roots(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_unmanaged_submission_surface=True,
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "unmanaged_submission_surface_present" in report["blockers"]
    assert report["unmanaged_submission_surface_roots"] == [
        str((quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "submission_pituitary").resolve())
    ]
def test_build_gate_report_accepts_archived_reference_only_legacy_submission_surface(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_unmanaged_submission_surface=True,
        archive_legacy_submission_surface=True,
        include_current_medical_publication_surface_report=True,
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "clear"
    assert report["blockers"] == []
    assert report["unmanaged_submission_surface_roots"] == []
    assert report["archived_submission_surface_roots"] == [
        str((quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "submission_pituitary").resolve())
    ]
def test_build_gate_report_blocks_archived_reference_only_surface_when_target_manifest_is_outside_current_paper(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_unmanaged_submission_surface=True,
        archive_legacy_submission_surface=True,
    )
    external_manifest = tmp_path / "external" / "paper" / "submission_minimal" / "submission_manifest.json"
    dump_json(
        external_manifest,
        {
            "schema_version": 1,
            "publication_profile": "general_medical_journal",
        },
    )
    archived_manifest_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "paper-run-1"
        / "paper"
        / "submission_pituitary"
        / "submission_manifest.json"
    )
    payload = json.loads(archived_manifest_path.read_text(encoding="utf-8"))
    payload["active_managed_submission_manifest_path"] = str(external_manifest.resolve())
    dump_json(archived_manifest_path, payload)

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "unmanaged_submission_surface_present" in report["blockers"]
    assert report["archived_submission_surface_roots"] == []
    assert report["unmanaged_submission_surface_roots"] == [
        str((quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "submission_pituitary").resolve())
    ]
def test_build_gate_report_blocks_forbidden_manuscript_terminology(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        manuscript_files={
            "build/review_manuscript.md": "Methods: we analyzed the locked v2026-03-31 dataset.\n",
            "submission_minimal/tables/Table1.md": (
                "Note: the paper-facing mainline analysis used the workspace cohort and "
                "the 2024-06-30 follow-up freeze.\n"
            ),
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "forbidden_manuscript_terminology" in report["blockers"]
    violations = report["manuscript_terminology_violations"]
    assert any(
        item["path"].endswith("build/review_manuscript.md")
        and item["label"] == "locked_dataset_version_label"
        and item["match"] == "locked v2026-03-31"
        for item in violations
    )
    assert any(
        item["path"].endswith("submission_minimal/tables/Table1.md")
        and item["label"] == "internal_editorial_label"
        and item["match"] == "paper-facing"
        for item in violations
    )
    assert any(
        item["path"].endswith("submission_minimal/tables/Table1.md")
        and item["label"] == "internal_editorial_label"
        and item["match"] == "mainline"
        for item in violations
    )
    assert any(
        item["path"].endswith("submission_minimal/tables/Table1.md")
        and item["label"] == "workspace_cohort_label"
        and item["match"] == "workspace cohort"
        for item in violations
    )
    assert any(
        item["path"].endswith("submission_minimal/tables/Table1.md")
        and item["label"] == "followup_freeze_label"
        and item["match"] == "follow-up freeze"
        for item in violations
    )
def test_build_gate_report_blocks_submission_surface_qc_failures(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        figure_catalog={
            "schema_version": 1,
            "figures": [],
        },
    )
    submission_manifest_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "paper-run-1"
        / "paper"
        / "submission_minimal"
        / "submission_manifest.json"
    )
    payload = json.loads(submission_manifest_path.read_text(encoding="utf-8"))
    payload["figures"] = [
        {
            "figure_id": "GA1",
            "template_id": "submission_graphical_abstract",
            "qc_profile": "submission_graphical_abstract",
            "qc_result": {
                "status": "fail",
                "qc_profile": "submission_graphical_abstract",
                "failure_reason": "panel_text_out_of_panel",
                "audit_classes": ["layout"],
            },
        }
    ]
    submission_manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert report["allow_write"] is False
    assert "submission_surface_qc_failure_present" in report["blockers"]
    assert report["submission_surface_qc_failures"] == [
        {
            "collection": "figures",
            "item_id": "GA1",
            "descriptor": "submission_graphical_abstract",
            "qc_profile": "submission_graphical_abstract",
            "failure_reason": "panel_text_out_of_panel",
            "audit_classes": ["layout"],
        }
    ]
def test_build_gate_report_blocks_submission_manuscript_surface_without_embedded_figures(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_current_medical_publication_surface_report=True,
        include_submission_authority_inputs=False,
        figure_catalog={
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "paper_role": "main_text",
                    "manuscript_status": "main_text",
                }
            ],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "submission_surface_qc_failure_present" in report["blockers"]
    failure_reasons = {item["failure_reason"] for item in report["submission_surface_qc_failures"]}
    assert "submission_source_markdown_missing" in failure_reasons
    assert "submission_docx_missing_embedded_figures" in failure_reasons
    assert "submission_pdf_missing_embedded_figures" in failure_reasons
def test_build_gate_report_infers_general_profile_for_legacy_submission_manifest(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_current_medical_publication_surface_report=True,
        figure_catalog={
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "paper_role": "main_text",
                }
            ],
        },
    )
    submission_manifest_path = (
        quest_root
        / ".ds"
        / "worktrees"
        / "paper-run-1"
        / "paper"
        / "submission_minimal"
        / "submission_manifest.json"
    )
    payload = json.loads(submission_manifest_path.read_text(encoding="utf-8"))
    payload.pop("publication_profile", None)
    payload["manuscript"] = {
        "docx_path": "paper/submission_minimal/manuscript.docx",
        "pdf_path": "paper/submission_minimal/paper.pdf",
    }
    submission_manifest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    failure_reasons = {item["failure_reason"] for item in report["submission_surface_qc_failures"]}
    assert "submission_source_markdown_missing" in failure_reasons
    assert "submission_docx_missing_embedded_figures" in failure_reasons
    assert "submission_pdf_missing_embedded_figures" in failure_reasons
def test_build_gate_report_inherits_blocked_medical_publication_surface_status(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    dump_json(
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:32Z.json",
        {
            "status": "blocked",
            "blockers": ["figure_catalog_missing_or_incomplete"],
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert report["allow_write"] is False
    assert report["medical_publication_surface_status"] == "blocked"
    assert "medical_publication_surface_blocked" in report["blockers"]
    assert report["medical_publication_surface_report_path"].endswith(
        "artifacts/reports/medical_publication_surface/2026-04-05T15:29:32Z.json"
    )
def test_build_gate_report_blocks_when_study_charter_is_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    study_root = tmp_path / "studies" / "002-early-residual-risk"
    (study_root / "artifacts" / "controller" / "study_charter.json").unlink()

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert report["allow_write"] is False
    assert report["charter_contract_linkage_status"] == "study_charter_missing"
    assert "study_charter_missing" in report["blockers"]
    assert report["current_required_action"] == "return_to_publishability_gate"
    assert "stable study charter artifact is missing" in report["controller_stage_note"]
def test_build_gate_report_blocks_when_study_charter_is_invalid(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(tmp_path, include_submission_minimal=True)
    study_root = tmp_path / "studies" / "002-early-residual-risk"
    (study_root / "artifacts" / "controller" / "study_charter.json").write_text("{invalid\n", encoding="utf-8")

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert report["allow_write"] is False
    assert report["charter_contract_linkage_status"] == "study_charter_invalid"
    assert "study_charter_invalid" in report["blockers"]
    assert report["current_required_action"] == "return_to_publishability_gate"
    assert "stable study charter artifact is invalid" in report["controller_stage_note"]
def test_build_gate_report_maps_surface_signals_to_named_controller_blockers(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_report={
            "status": "blocked",
            "blockers": [
                "review_ledger_missing_or_incomplete",
                "claim_evidence_map_missing_or_incomplete",
                "public_evidence_decisions_missing_or_incomplete",
            ],
            "review_ledger_valid": False,
            "claim_evidence_map_valid": False,
            "evidence_ledger_valid": False,
            "medical_story_contract_valid": False,
            "public_evidence_decision_count": 0,
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "medical_publication_surface_blocked" in report["blockers"]
    assert "reviewer_first_concerns_unresolved" in report["blockers"]
    assert "claim_evidence_consistency_failed" in report["blockers"]
    assert "submission_hardening_incomplete" in report["blockers"]
    assert report["medical_publication_surface_named_blockers"] == [
        "reviewer_first_concerns_unresolved",
        "claim_evidence_consistency_failed",
        "submission_hardening_incomplete",
    ]
    assert report["medical_publication_surface_route_back_recommendation"] == "return_to_write"
    assert report["supervisor_phase"] == "publishability_gate_blocked"
    assert report["bundle_tasks_downstream_only"] is True
    assert report["current_required_action"] == "return_to_publishability_gate"
    assert "route back to `write` to close reviewer-first publication-surface concerns" in report[
        "controller_stage_note"
    ]
    assert "reviewer-first hardening" not in report["controller_stage_note"]
def test_build_gate_report_projects_surface_charter_expectation_gaps(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    evidence_gap_text = "External validation evidence package is durably archived for the manuscript route."
    review_gap_text = "Residual-risk framing is defended against calibration drift before submission."
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_report={
            "status": "blocked",
            "blockers": ["charter_expectation_closure_incomplete"],
            "charter_expectation_closure_summary": {
                "status": "blocked",
                "blocking_items": [
                    {
                        "expectation_key": "minimum_sci_ready_evidence_package",
                        "expectation_text": evidence_gap_text,
                        "ledger_name": "evidence_ledger",
                        "ledger_path": "paper/evidence_ledger.json",
                        "contract_json_pointer": (
                            "/paper_quality_contract/evidence_expectations/minimum_sci_ready_evidence_package"
                        ),
                        "closure_status": "blocked",
                        "recorded": True,
                        "record_count": 1,
                        "blocker": True,
                    },
                    {
                        "expectation_key": "scientific_followup_questions",
                        "expectation_text": review_gap_text,
                        "ledger_name": "review_ledger",
                        "ledger_path": "paper/review/review_ledger.json",
                        "contract_json_pointer": (
                            "/paper_quality_contract/review_expectations/scientific_followup_questions"
                        ),
                        "closure_status": "open",
                        "recorded": True,
                        "record_count": 1,
                        "blocker": True,
                    },
                ],
            },
        },
    )

    report = module.build_gate_report(module.build_gate_state(quest_root))
    gaps = report["medical_publication_surface_expectation_gaps"]

    assert report["status"] == "blocked"
    assert "medical_publication_surface_blocked" in report["blockers"]
    assert "charter_expectation_closure_incomplete" in report["blockers"]
    assert report["medical_publication_surface_named_blockers"] == [
        "reviewer_first_concerns_unresolved",
        "claim_evidence_consistency_failed",
    ]
    assert report["medical_publication_surface_route_back_recommendation"] == "return_to_write"
    assert [gap["expectation_key"] for gap in gaps] == [
        "minimum_sci_ready_evidence_package",
        "scientific_followup_questions",
    ]
    assert {gap["expectation_text"] for gap in gaps} == {evidence_gap_text, review_gap_text}
    assert {gap["ledger_name"] for gap in gaps} == {"evidence_ledger", "review_ledger"}
    assert {gap["closure_status"] for gap in gaps} == {"blocked", "open"}
    assert {gap["contract_json_pointer"] for gap in gaps} == {
        "/paper_quality_contract/evidence_expectations/minimum_sci_ready_evidence_package",
        "/paper_quality_contract/review_expectations/scientific_followup_questions",
    }

    markdown = module.render_gate_markdown(report)
    assert "## Medical Publication Surface Expectation Gaps" in markdown
    assert evidence_gap_text in markdown
    assert review_gap_text in markdown
    assert "contract_json_pointer=`/paper_quality_contract/evidence_expectations/minimum_sci_ready_evidence_package`" in markdown
    assert "contract_json_pointer=`/paper_quality_contract/review_expectations/scientific_followup_questions`" in markdown
    assert "ledger=`evidence_ledger`" in markdown
    assert "ledger=`review_ledger`" in markdown
def test_build_gate_report_routes_each_surface_blocker_to_core_controller_route(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")

    reviewer_first_root = make_quest(
        tmp_path / "reviewer-first",
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_report={
            "status": "blocked",
            "blockers": ["review_ledger_missing_or_incomplete"],
        },
    )
    reviewer_first_report = module.build_gate_report(module.build_gate_state(reviewer_first_root))

    assert reviewer_first_report["medical_publication_surface_named_blockers"] == [
        "reviewer_first_concerns_unresolved"
    ]
    assert reviewer_first_report["medical_publication_surface_route_back_recommendation"] == "return_to_write"
    assert "route back to `write` to close reviewer-first publication-surface concerns" in reviewer_first_report[
        "controller_stage_note"
    ]
    assert "reviewer-first hardening" not in reviewer_first_report["controller_stage_note"]

    claim_evidence_root = make_quest(
        tmp_path / "claim-evidence",
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_report={
            "status": "blocked",
            "blockers": ["claim_evidence_map_missing_or_incomplete"],
        },
    )
    claim_evidence_report = module.build_gate_report(module.build_gate_state(claim_evidence_root))

    assert claim_evidence_report["medical_publication_surface_named_blockers"] == [
        "claim_evidence_consistency_failed"
    ]
    assert (
        claim_evidence_report["medical_publication_surface_route_back_recommendation"]
        == "return_to_analysis_campaign"
    )
    assert "route back to `analysis-campaign` to close claim-evidence consistency gaps" in claim_evidence_report[
        "controller_stage_note"
    ]
    assert "claim-evidence hardening" not in claim_evidence_report["controller_stage_note"]

    submission_hardening_root = make_quest(
        tmp_path / "submission-hardening",
        include_submission_minimal=True,
        include_main_result=True,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_report={
            "status": "blocked",
            "blockers": ["public_evidence_decisions_missing_or_incomplete"],
        },
    )
    main_result_path = (
        submission_hardening_root
        / ".ds"
        / "worktrees"
        / "paper-run-1"
        / "experiments"
        / "main"
        / "run-1"
        / "RESULT.json"
    )
    gate_report_path = submission_hardening_root / "artifacts" / "reports" / "publishability_gate" / "2026-04-17T000000Z.json"
    dump_json(
        gate_report_path,
        {
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-17T00:00:00+00:00",
            "status": "clear",
            "allow_write": False,
            "blockers": [],
        },
    )
    os.utime(main_result_path, (1, 1))
    os.utime(gate_report_path, (3, 3))
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    submission_hardening_report = module.build_gate_report(module.build_gate_state(submission_hardening_root))

    assert submission_hardening_report["medical_publication_surface_named_blockers"] == [
        "submission_hardening_incomplete"
    ]
    assert submission_hardening_report["medical_publication_surface_route_back_recommendation"] == "return_to_finalize"
    assert submission_hardening_report["supervisor_phase"] == "bundle_stage_blocked"
    assert submission_hardening_report["bundle_tasks_downstream_only"] is False
    assert submission_hardening_report["current_required_action"] == "complete_bundle_stage"
    assert "route back to `finalize` to close submission-readiness gaps" in submission_hardening_report[
        "controller_stage_note"
    ]
    assert "submission hardening" not in submission_hardening_report["controller_stage_note"]
def test_build_gate_report_keeps_named_surface_blockers_clear_when_surface_is_clear(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    monkeypatch.setattr(module, "collect_submission_surface_qc_failures", lambda *args, **kwargs: [])
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
        runtime_status="waiting_for_user",
        include_current_medical_publication_surface_report=True,
        medical_publication_surface_report={
            "status": "clear",
            "blockers": [],
            "review_ledger_valid": True,
            "claim_evidence_map_valid": True,
            "evidence_ledger_valid": True,
            "medical_story_contract_valid": True,
            "public_evidence_decision_count": 2,
        },
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "clear"
    assert "medical_publication_surface_blocked" not in report["blockers"]
    assert "reviewer_first_concerns_unresolved" not in report["blockers"]
    assert "claim_evidence_consistency_failed" not in report["blockers"]
    assert "submission_hardening_incomplete" not in report["blockers"]
    assert report["medical_publication_surface_named_blockers"] == []
    assert report["medical_publication_surface_route_back_recommendation"] is None
def test_build_gate_report_ignores_newer_surface_report_from_other_paper_line(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_current_medical_publication_surface_report=True,
    )
    current_report_path = (
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:32Z.json"
    )
    anchor_path = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper" / "paper_bundle_manifest.json"
    dump_json(
        quest_root / "paper" / "paper_line_state.json",
        {
            "paper_root": str((quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper").resolve()),
        },
    )
    dump_json(
        current_report_path,
        {
            "paper_root": str((quest_root / "paper").resolve()),
            "status": "clear",
            "blockers": [],
        },
    )
    current_time = anchor_path.stat().st_mtime + 1
    os.utime(current_report_path, (current_time, current_time))

    stale_report_path = (
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:33Z.json"
    )
    dump_json(
        stale_report_path,
        {
            "paper_root": str(
                (quest_root / ".ds" / "worktrees" / "analysis-public-evidence-run-2" / "paper").resolve()
            ),
            "status": "blocked",
            "blockers": ["figure_catalog_missing_or_incomplete"],
        },
    )
    stale_time = current_time + 10
    os.utime(stale_report_path, (stale_time, stale_time))

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["medical_publication_surface_status"] == "clear"
    assert report["medical_publication_surface_current"] is True
    assert "medical_publication_surface_blocked" not in report["blockers"]
    assert report["medical_publication_surface_report_path"].endswith(
        "artifacts/reports/medical_publication_surface/2026-04-05T15:29:32Z.json"
    )
def test_build_gate_report_falls_back_to_same_study_surface_report_when_paper_root_drifted(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
    )
    study_root = tmp_path / "studies" / "002-early-residual-risk"
    worktree_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    drifted_paper_root = quest_root / ".ds" / "worktrees" / "analysis-run-2" / "paper"
    drifted_paper_root.mkdir(parents=True, exist_ok=True)
    surface_report_path = (
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:34Z.json"
    )
    dump_json(
        surface_report_path,
        {
            "study_root": str(study_root.resolve()),
            "paper_root": str(drifted_paper_root.resolve()),
            "status": "clear",
            "blockers": [],
        },
    )
    anchor_path = worktree_paper_root / "paper_bundle_manifest.json"
    fresh_time = anchor_path.stat().st_mtime + 10
    os.utime(surface_report_path, (fresh_time, fresh_time))

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert state.paper_root == worktree_paper_root.resolve()
    assert report["medical_publication_surface_report_path"] == str(surface_report_path)
    assert report["medical_publication_surface_status"] == "clear"
    assert report["medical_publication_surface_current"] is True
    assert "missing_current_medical_publication_surface_report" not in report["blockers"]
    assert "medical_publication_surface_blocked" not in report["blockers"]
def test_build_gate_report_uses_authoritative_bundle_manifest_for_surface_currentness_when_projected_mirror_is_newer(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
    )
    authoritative_paper_root = quest_root / ".ds" / "worktrees" / "paper-run-1" / "paper"
    projected_paper_root = quest_root / "paper"
    analysis_paper_root = quest_root / ".ds" / "worktrees" / "analysis-run-1" / "paper"
    analysis_paper_root.mkdir(parents=True, exist_ok=True)

    dump_json(
        projected_paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "paper_branch": "paper/main",
            "compile_report_path": "paper/build/compile_report.json",
            "bundle_inputs": {
                "compiled_markdown_path": "paper/build/review_manuscript.md",
            },
        },
    )
    dump_json(
        projected_paper_root / "paper_line_state.json",
        {
            "schema_version": 1,
            "paper_branch": "analysis/paper-drifted",
            "paper_root": str(analysis_paper_root.resolve()),
        },
    )
    surface_report_path = (
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "2026-04-05T15:29:32Z.json"
    )
    dump_json(
        surface_report_path,
        {
            "paper_root": str(authoritative_paper_root.resolve()),
            "status": "clear",
            "blockers": [],
        },
    )

    authoritative_manifest_path = authoritative_paper_root / "paper_bundle_manifest.json"
    projected_manifest_path = projected_paper_root / "paper_bundle_manifest.json"
    base_time = authoritative_manifest_path.stat().st_mtime + 10
    os.utime(authoritative_manifest_path, (base_time, base_time))
    os.utime(surface_report_path, (base_time + 10, base_time + 10))
    os.utime(projected_manifest_path, (base_time + 20, base_time + 20))

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert state.paper_bundle_manifest_path == projected_manifest_path
    assert state.paper_root == authoritative_paper_root.resolve()
    assert report["medical_publication_surface_report_path"] == str(surface_report_path)
    assert report["medical_publication_surface_current"] is True
    assert "missing_current_medical_publication_surface_report" not in report["blockers"]


def test_publication_gate_intervention_allows_bounded_submission_hardening_finalize() -> None:
    policy = importlib.import_module("med_autoscience.policies.publication_gate")

    message = policy.build_intervention_message(
        {
            "run_id": "run-001",
            "blockers": ["medical_publication_surface_blocked", "submission_hardening_incomplete"],
            "missing_non_scalar_deliverables": [],
            "headline_metrics": {},
            "medical_publication_surface_route_back_recommendation": "return_to_finalize",
        }
    )

    assert "bounded `finalize` / submission-hardening pass" in message
    assert "Do not continue write" not in message
    assert "new analysis campaigns" in message


def test_submission_hardening_with_stale_package_stays_on_bundle_path() -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")

    state = module.build_publication_supervisor_state(
        anchor_kind="paper_bundle",
        allow_write=False,
        blockers=[
            "stale_submission_minimal_authority",
            "medical_publication_surface_blocked",
            "submission_hardening_incomplete",
            "submission_surface_qc_failure_present",
        ],
        medical_publication_surface_named_blockers=["submission_hardening_incomplete"],
        bundle_stage_ready=True,
    )

    assert state["supervisor_phase"] == "bundle_stage_blocked"
    assert state["bundle_tasks_downstream_only"] is False
    assert state["current_required_action"] == "complete_bundle_stage"


def test_submission_hardening_intervention_allows_bounded_finalize_with_package_sync() -> None:
    module = importlib.import_module("med_autoscience.policies.publication_gate")

    message = module.build_intervention_message(
        {
            "run_id": "run-hardening",
            "blockers": [
                "stale_submission_minimal_authority",
                "medical_publication_surface_blocked",
                "submission_hardening_incomplete",
                "submission_surface_qc_failure_present",
            ],
            "medical_publication_surface_route_back_recommendation": "return_to_finalize",
            "missing_non_scalar_deliverables": [],
            "headline_metrics": {},
        }
    )

    assert "bounded `finalize` / submission-hardening pass" in message
    assert "Do not continue write" not in message
    assert "rebuild submission_minimal" in message
