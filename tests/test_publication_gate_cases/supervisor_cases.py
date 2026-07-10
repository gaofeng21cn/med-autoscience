from __future__ import annotations

from tests.test_publication_gate_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

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
        str((quest_root / "paper" / "submission_pituitary").resolve())
    ]
def test_build_gate_report_accepts_archived_reference_only_legacy_submission_surface(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    bypass_submission_surface_qc(monkeypatch)
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
        str((quest_root / "paper" / "submission_pituitary").resolve())
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
        str((quest_root / "paper" / "submission_pituitary").resolve())
    ]
def test_build_gate_report_blocks_forbidden_manuscript_terminology(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        manuscript_files={
            "build/review_manuscript.md": (
                "Methods: we analyzed the locked v2026-03-31 dataset. Candidate domains "
                "were selected before manuscript repair, then reviewed by the AI reviewer "
                "after quality repair and publication gate routing.\n"
            ),
            "submission_minimal/tables/Table1.md": (
                "Note: the paper-facing mainline analysis used the workspace cohort and "
                "the 2024-06-30 follow-up freeze. This table does not imply submission readiness.\n"
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
    assert any(
        item["path"].endswith("build/review_manuscript.md")
        and item["label"] == "internal_runtime_or_repair_process_language"
        and item["match"] == "before manuscript repair"
        for item in violations
    )
    assert any(
        item["path"].endswith("build/review_manuscript.md")
        and item["label"] == "internal_runtime_or_repair_process_language"
        and item["match"] == "AI reviewer"
        for item in violations
    )
    assert any(
        item["path"].endswith("build/review_manuscript.md")
        and item["label"] == "internal_runtime_or_repair_process_language"
        and item["match"] == "quality repair"
        for item in violations
    )
    assert any(
        item["path"].endswith("build/review_manuscript.md")
        and item["label"] == "internal_runtime_or_repair_process_language"
        and item["match"] == "publication gate"
        for item in violations
    )
    assert any(
        item["path"].endswith("submission_minimal/tables/Table1.md")
        and item["label"] == "internal_runtime_or_repair_process_language"
        and item["match"] == "submission readiness"
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
    blocking_artifact_refs_text = json.dumps(report["blocking_artifact_refs"], sort_keys=True)
    assert '"source_path"' in blocking_artifact_refs_text
    assert "reviewer_first_concerns_unresolved" in blocking_artifact_refs_text
    assert "paper/review/review_ledger.json" in blocking_artifact_refs_text
    assert "claim_evidence_consistency_failed" in blocking_artifact_refs_text
    assert "paper/claim_evidence_map.json" in blocking_artifact_refs_text
    assert "submission_hardening_incomplete" in blocking_artifact_refs_text
    assert (
        "paper/submission_minimal/submission_manifest.json"
        in blocking_artifact_refs_text
    )
def test_build_gate_report_keeps_named_surface_blockers_clear_when_surface_is_clear(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    bypass_submission_surface_qc(monkeypatch)
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
    projected_paper_root = quest_root / "paper"
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
    anchor_path = projected_paper_root / "paper_bundle_manifest.json"
    fresh_time = anchor_path.stat().st_mtime + 10
    os.utime(surface_report_path, (fresh_time, fresh_time))

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert state.paper_root == projected_paper_root.resolve()
    assert report["medical_publication_surface_report_path"] == str(surface_report_path)
    assert report["medical_publication_surface_status"] == "clear"
    assert report["medical_publication_surface_current"] is True
    assert "missing_current_medical_publication_surface_report" not in report["blockers"]
    assert "medical_publication_surface_blocked" not in report["blockers"]
def test_build_gate_report_marks_surface_stale_when_projected_manifest_is_newer(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.publication_gate")
    quest_root = make_quest(
        tmp_path,
        include_submission_minimal=True,
        include_main_result=False,
    )
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
            "paper_root": str(projected_paper_root.resolve()),
            "status": "clear",
            "blockers": [],
        },
    )

    projected_manifest_path = projected_paper_root / "paper_bundle_manifest.json"
    base_time = projected_manifest_path.stat().st_mtime + 10
    os.utime(surface_report_path, (base_time + 10, base_time + 10))
    os.utime(projected_manifest_path, (base_time + 20, base_time + 20))

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert state.paper_bundle_manifest_path == projected_manifest_path
    assert state.paper_root == projected_paper_root.resolve()
    assert report["medical_publication_surface_report_path"] == str(surface_report_path)
    assert report["medical_publication_surface_current"] is False
    assert "missing_current_medical_publication_surface_report" in report["blockers"]


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
