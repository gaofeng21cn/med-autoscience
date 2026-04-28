from __future__ import annotations

from . import shared as _shared
from .runtime_projection_basics import _write_runtime_efficiency_fixture


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_progress_operator_view_surfaces_noop_suppression_and_runtime_efficiency(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    _write_publication_eval(study_root, quest_root)
    telemetry_path, evidence_index_path = _write_runtime_efficiency_fixture(quest_root)
    runtime_watch_path = quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"
    _write_json(
        runtime_watch_path,
        {
            "schema_version": 1,
            "scanned_at": "2026-04-28T10:00:00+00:00",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "controllers": {
                "publication_gate": {
                    "status": "blocked",
                    "action": "suppressed",
                    "blockers": ["claim_evidence_consistency_failed"],
                    "suppression_reason": "unchanged_fingerprint",
                    "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                }
            },
            "managed_study_no_op_suppressions": [
                {
                    "study_id": "001-risk",
                    "quest_id": "quest-001",
                    "outcome": "skipped_matching_work_unit",
                    "reason": "outer-loop work unit already dispatched for the same blocker fingerprint",
                    "dedupe_scope": "controller_decision_blocker_authority",
                    "work_unit_fingerprint": "publication-blockers::same",
                    "next_work_unit": {
                        "unit_id": "analysis_claim_evidence_repair",
                        "lane": "analysis-campaign",
                        "summary": "Repair claim-evidence blockers.",
                    },
                    "operator_summary": "同一 blocker fingerprint 已执行过同一 controller work unit；继续空转不会增加论文证据。",
                }
            ],
            "runtime_efficiency": {
                "run_id": "run-001",
                "evidence_packet_index_path": str(evidence_index_path),
                "evidence_packet_count": 1,
                "latest_evidence_packets": [
                    {
                        "tool_name": "bash_exec",
                        "detail": "compact",
                        "summary": "bash_exec: log_line_count=1200; key_blockers=1",
                        "sidecar_path": str(evidence_index_path.parent / "bash_exec-large-log.json"),
                    }
                ],
                "gate_cache_surfaces": [
                    {
                        "surface_id": "publication_gate",
                        "input_fingerprint": "publication-gate-fp-1",
                    }
                ],
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
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "blocked",
            "reason": "study_completion_publishability_gate_blocked",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["runtime_efficiency"]["telemetry_path"] == str(telemetry_path)
    assert result["runtime_efficiency"]["tool_result_bytes_saved_total"] == 86420
    assert result["operator_status_card"]["no_op_suppression"]["outcome"] == "skipped_matching_work_unit"
    assert "继续空转不会增加论文证据" in result["operator_status_card"]["current_focus"]
    assert "evidence packet" in result["operator_status_card"]["runtime_efficiency_summary"]
    assert result["operator_status_card"]["runtime_efficiency_refs"]["evidence_packet_index_path"] == str(evidence_index_path)
