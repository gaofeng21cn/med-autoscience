from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_progress_projects_newer_runtime_medical_publication_surface_when_study_shadow_is_ready(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    mcp_projection = importlib.import_module("med_autoscience.mcp_server_parts.study_progress_projection")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-risk",
        quest_id="quest-002",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    runtime_surface_path = (
        quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"
    )
    _write_json(
        runtime_surface_path,
        {
            "schema_version": 1,
            "gate_kind": "medical_publication_surface_control",
            "generated_at": "2026-05-27T17:26:18+00:00",
            "quest_id": "quest-002",
            "status": "blocked",
            "recommended_action": "return_to_write",
            "blockers": [
                "figure_layout_sidecar_missing_or_incomplete",
                "reference_citation_coverage_incomplete",
            ],
            "paper_root": str(study_root / "paper"),
            "study_root": str(study_root),
            "figure_catalog_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
            "top_hits": [
                {
                    "path": str(study_root / "paper" / "figures" / "figure5_layout.json"),
                    "location": "layout_boxes[10]",
                    "pattern_id": "figure_layout_box_invalid_extent",
                    "phrase": "F5",
                    "excerpt": "Figure `F5` layout box has non-positive width or height.",
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "medical_publication_surface" / "latest.json",
        {
            "schema_version": 1,
            "status": "ready",
            "updated_at": "2026-05-27T15:00:00+00:00",
        },
    )
    _write_json(
        quest_root / "artifacts" / "reports" / "domain_health_diagnostic" / "latest.json",
        {
            "schema_version": 1,
            "scanned_at": "2026-05-27T17:26:18+00:00",
            "quest_root": str(quest_root),
            "quest_status": "active",
            "controllers": {
                "medical_publication_surface": {
                    "status": "blocked",
                    "action": "suppressed",
                    "blockers": [
                        "figure_layout_sidecar_missing_or_incomplete",
                        "reference_citation_coverage_incomplete",
                    ],
                    "report_json": str(runtime_surface_path),
                    "suppression_reason": "apply_disabled",
                },
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": "publication-eval::002-risk::quest-002::2026-05-27T15:00:00+00:00",
            "study_id": "002-risk",
            "quest_id": "quest-002",
            "emitted_at": "2026-05-27T15:00:00+00:00",
            "verdict": {"overall_verdict": "promising", "summary": "旧 study shadow 仍显示 ready。"},
            "gaps": [],
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "002-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "active",
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "quest_waiting_opl_runtime_owner_route",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "current_required_action": "return_to_publishability_gate",
                "controller_stage_note": "论文稿面仍有医学论文表达硬阻塞。",
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "active_run_id": None,
                "current_required_action": "supervise_runtime_only",
                "publication_gate_allows_direct_write": False,
            },
            "continuation_state": {
                "quest_status": "active",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "MAS 外环监管心跳新鲜。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="002-risk")
    compact = mcp_projection.compact_study_progress_projection(result)

    surface = result["runtime_medical_publication_surface"]
    assert surface["authority"] == "runtime_report_projection_only"
    assert surface["status"] == "blocked"
    assert surface["source_path"] == str(runtime_surface_path)
    assert surface["study_shadow"]["status"] == "ready"
    assert surface["blockers"] == [
        "figure_layout_sidecar_missing_or_incomplete",
        "reference_citation_coverage_incomplete",
    ]
    assert surface["top_hits"][0]["pattern_id"] == "figure_layout_box_invalid_extent"
    assert result["refs"]["runtime_medical_publication_surface_report_path"] == str(runtime_surface_path)
    assert "图表布局 sidecar 仍不完整。" in result["current_blockers"]
    assert "参考文献引用覆盖仍不完整。" in result["current_blockers"]
    assert "图表布局 sidecar 仍不完整。" in result["user_visible_projection"]["current_blockers"]
    assert "参考文献引用覆盖仍不完整。" in result["status_narration_contract"]["current_blockers"]
    assert compact["runtime_medical_publication_surface"]["status"] == "blocked"
    assert compact["runtime_medical_publication_surface"]["study_shadow"]["status"] == "ready"
    assert compact["runtime_medical_publication_surface"]["top_hits"][0]["phrase"] == "F5"


def test_runtime_medical_publication_surface_projects_structured_and_invalid_blockers(
    tmp_path: Path,
) -> None:
    surface = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.runtime_medical_publication_surface"
    )
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-risk", quest_id="quest-002")
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    runtime_surface_path = quest_root / "artifacts" / "reports" / "medical_publication_surface" / "latest.json"
    _write_json(
        runtime_surface_path,
        {
            "schema_version": 1,
            "status": "blocked",
            "blockers": [
                {
                    "id": "table_figure_claim_map_missing_or_incomplete",
                    "source_path": str(study_root / "paper" / "figures" / "figure_catalog.json"),
                },
                {"source_path": str(study_root / "paper" / "claim_evidence_map.json")},
            ],
        },
    )

    result = surface.build_runtime_medical_publication_surface_projection(
        study_root=study_root,
        quest_root=quest_root,
        domain_health_diagnostic_payload=None,
    )

    assert result is not None
    assert result["status"] == "blocked"
    assert result["blockers"] == [
        "table_figure_claim_map_missing_or_incomplete",
        "invalid_blocker_payload",
    ]
    assert result["blocker_summaries"] == [
        "table_figure_claim_map_missing_or_incomplete".replace("_", " "),
        "invalid_blocker_payload",
    ]
