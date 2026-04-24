from .shared import *

def test_run_controller_stops_then_enqueues_medical_surface_message(tmp_path: Path, monkeypatch) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, medicalized=False, ama_defaults=False)
    stopped: list[tuple[str | None, str | None, str, str]] = []

    def fake_stop_quest(
        *,
        daemon_url: str | None = None,
        runtime_root: Path | None = None,
        quest_id: str,
        source: str,
    ) -> dict:
        stopped.append((daemon_url, str(runtime_root) if runtime_root is not None else None, quest_id, source))
        return {"ok": True, "status": "stopped", "source": source}

    monkeypatch.setattr(module.managed_runtime_transport, "stop_quest", fake_stop_quest)

    result = module.run_controller(
        quest_root=quest_root,
        apply=True,
        daemon_url="http://127.0.0.1:20999",
    )

    assert module.managed_runtime_transport is module.med_deepscientist_transport
    assert stopped == [
        (
            "http://127.0.0.1:20999",
            str((quest_root.parent.parent).resolve()),
            "002-early-residual-risk",
            "codex-medical-publication-surface",
        )
    ]
    assert result["intervention_enqueued"] is True
    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    assert len(queue["pending"]) == 1
    content = queue["pending"][0]["content"]
    assert "deployment-facing" in content
    assert "Do not advertise tooling in figure captions." in content
    assert "AMA" in content
    assert "methods_implementation_manifest.json" in content
    assert "results_narrative_map.json" in content
    assert "figure_semantics_manifest.json" in content
    assert "evidence_ledger.json" in content
    assert "derived_analysis_manifest.json" in content
    assert "manuscript_safe_reproducibility_supplement.json" in content
    assert "endpoint_provenance_note.md" in content
    assert result["top_hits"]


def test_run_controller_without_daemon_url_enqueues_but_does_not_stop(tmp_path: Path, monkeypatch) -> None:
    try:
        module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    except ModuleNotFoundError:
        module = None

    assert module is not None
    quest_root = make_quest(tmp_path, medicalized=False, ama_defaults=False)
    stopped: list[tuple[str | None, str | None, str, str]] = []

    def fake_stop_quest(
        *,
        daemon_url: str | None = None,
        runtime_root: Path | None = None,
        quest_id: str,
        source: str,
    ) -> dict:
        stopped.append((daemon_url, str(runtime_root) if runtime_root is not None else None, quest_id, source))
        return {"ok": True, "status": "stopped", "source": source}

    monkeypatch.setattr(module.managed_runtime_transport, "stop_quest", fake_stop_quest)

    result = module.run_controller(
        quest_root=quest_root,
        apply=True,
        daemon_url=None,
    )

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    assert stopped == []
    assert result["stop_result"] is None
    assert result["intervention_enqueued"] is True
    assert len(queue["pending"]) == 1


def test_build_surface_state_uses_runtime_protocol_quest_state(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    seen: dict[str, object] = {}

    def fake_load_runtime_state(path: Path) -> dict[str, object]:
        seen["quest_root"] = path
        return {"status": "patched", "quest_id": quest_root.name}

    monkeypatch.setattr(module.quest_state, "load_runtime_state", fake_load_runtime_state)

    state = module.build_surface_state(quest_root)

    assert seen == {"quest_root": quest_root}
    assert state.runtime_state["status"] == "patched"


def test_build_surface_state_resolves_study_root_from_live_quest_paper(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    workspace_root = tmp_path / "workspace"
    quest_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "004-live-quest"
    paper_root = quest_root / "paper"
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": "004-live-quest",
            "status": "running",
        },
    )
    dump_json(
        paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "bundle_inputs": {
                "compiled_markdown_path": "paper/build/review_manuscript.md",
            },
        },
    )
    study_root = workspace_root / "studies" / "004-study"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 004-study\n", encoding="utf-8")
    (study_root / "runtime_binding.yaml").write_text(
        "schema_version: 1\n"
        "study_id: 004-study\n"
        "quest_id: 004-live-quest\n",
        encoding="utf-8",
    )

    state = module.build_surface_state(quest_root)

    assert state.study_root == study_root.resolve()


def test_build_surface_state_prefers_bundle_branch_over_drifted_projected_paper_line_state(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    drifted_paper_root = _paper_root_from_quest(quest_root)
    projected_paper_root = quest_root / "paper"
    authoritative_paper_root = quest_root / ".ds" / "worktrees" / "paper-main" / "paper"
    authoritative_paper_root.mkdir(parents=True, exist_ok=True)
    dump_json(
        authoritative_paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "paper_branch": "paper/main",
            "bundle_inputs": {
                "compiled_markdown_path": "paper/build/review_manuscript.md",
            },
        },
    )
    dump_json(
        projected_paper_root / "paper_bundle_manifest.json",
        {
            "schema_version": 1,
            "paper_branch": "paper/main",
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
            "paper_root": str(drifted_paper_root.resolve()),
        },
    )

    state = module.build_surface_state(quest_root)

    assert state.paper_root == authoritative_paper_root.resolve()


def test_write_surface_files_uses_runtime_protocol_report_store(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.medical_publication_surface")
    quest_root = make_quest(tmp_path, medicalized=True, ama_defaults=True)
    seen: dict[str, object] = {}

    def fake_write_timestamped_report(
        *,
        quest_root: Path,
        report_group: str,
        timestamp: str,
        report: dict[str, object],
        markdown: str,
    ) -> tuple[Path, Path]:
        seen["quest_root"] = quest_root
        seen["report_group"] = report_group
        seen["timestamp"] = timestamp
        seen["report"] = report
        seen["markdown"] = markdown
        return quest_root / "artifacts" / "reports" / report_group / "latest.json", quest_root / "artifacts" / "reports" / report_group / "latest.md"

    monkeypatch.setattr(module.runtime_protocol_report_store, "write_timestamped_report", fake_write_timestamped_report)

    report = {
        "generated_at": "2026-04-03T04:20:00+00:00",
        "quest_id": quest_root.name,
        "run_id": "run-1",
        "status": "blocked",
        "recommended_action": "stop",
        "blockers": ["forbidden_tool_disclosure_in_caption"],
        "top_hits": [],
        "ama_defaults_present": True,
        "ama_csl_present": True,
        "ama_pdf_defaults_present": True,
        "paper_pdf_present": True,
        "draft_present": True,
        "review_manuscript_present": True,
        "figure_catalog_present": True,
        "figure_catalog_valid": True,
        "table_catalog_present": True,
        "table_catalog_valid": True,
        "methods_implementation_manifest_present": True,
        "methods_implementation_manifest_valid": True,
        "review_ledger_present": True,
        "review_ledger_valid": True,
        "results_narrative_map_present": True,
        "results_narrative_map_valid": True,
        "figure_semantics_manifest_present": True,
        "figure_semantics_manifest_valid": True,
        "evidence_ledger_present": True,
        "evidence_ledger_valid": True,
        "derived_analysis_manifest_present": True,
        "derived_analysis_manifest_valid": True,
        "reproducibility_supplement_present": True,
        "reproducibility_supplement_valid": True,
        "missing_data_policy_consistent": True,
        "endpoint_provenance_note_present": True,
        "endpoint_provenance_note_valid": True,
        "endpoint_provenance_note_applied": True,
        "forbidden_hit_count": 1,
        "undefined_methodology_label_hit_count": 0,
        "results_narration_hit_count": 0,
    }

    json_path, md_path = module.write_surface_files(quest_root, report)

    assert seen["quest_root"] == quest_root
    assert seen["report_group"] == "medical_publication_surface"
    assert seen["timestamp"] == "2026-04-03T04:20:00+00:00"
    assert json_path.name == "latest.json"
    assert md_path.name == "latest.md"
