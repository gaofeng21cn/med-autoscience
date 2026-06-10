from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_domain_health_diagnostic_uses_domain_health_diagnostic_protocol_helpers(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    quest_root = make_quest(tmp_path, "q001", status="running")
    seen: dict[str, object] = {}

    def fake_load_domain_health_diagnostic_state(path: Path) -> object:
        seen["loaded"] = str(path)
        return module.domain_health_diagnostic_protocol.DomainHealthDiagnosticState(
            schema_version=1,
            updated_at=None,
            controllers={},
        )

    def fake_plan_controller_intervention(**kwargs) -> object:
        seen.setdefault("planned", []).append(kwargs)
        return module.domain_health_diagnostic_protocol.DomainHealthDiagnosticInterventionPlan(
            action=module.domain_health_diagnostic_protocol.DomainHealthDiagnosticControllerAction.APPLIED,
            should_apply=True,
            suppression_reason=None,
            controller_state=module.domain_health_diagnostic_protocol.DomainHealthDiagnosticControllerState(
                last_seen_fingerprint="fp-1",
                last_applied_fingerprint="fp-1",
                last_applied_at="2026-04-02T12:00:00+00:00",
                last_status="blocked",
                last_suppression_reason=None,
            ),
        )

    monkeypatch.setattr(
        module.domain_health_diagnostic_protocol,
        "load_domain_health_diagnostic_state",
        fake_load_domain_health_diagnostic_state,
    )
    monkeypatch.setattr(
        module.domain_health_diagnostic_protocol,
        "plan_controller_intervention",
        fake_plan_controller_intervention,
    )
    monkeypatch.setattr(
        module.domain_health_diagnostic_protocol,
        "save_domain_health_diagnostic_state",
        lambda quest_root, payload: seen.setdefault("saved", []).append((str(quest_root), payload)),
    )
    monkeypatch.setattr(
        module.domain_health_diagnostic_protocol,
        "write_domain_health_diagnostic_report",
        lambda *, quest_root, report, markdown: seen.setdefault("reported", []).append((str(quest_root), report))
        or (quest_root / "artifacts" / "reports" / "domain_health_diagnostic" / "latest.json", quest_root / "artifacts" / "reports" / "domain_health_diagnostic" / "latest.md"),
    )

    result = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "blocked",
                "blockers": ["missing_post_main_publishability_gate"],
                "allow_write": False,
                "missing_non_scalar_deliverables": ["calibration_plot"],
                "submission_minimal_present": False,
                "report_json": "dry.json",
                "report_markdown": "dry.md",
            }
        },
        apply=True,
    )

    assert seen["loaded"] == str(quest_root)
    assert len(seen["planned"]) == 1
    assert len(seen["saved"]) == 1
    assert len(seen["reported"]) == 1
    saved_state = seen["saved"][0][1]
    assert saved_state.controllers["publication_gate"].last_applied_fingerprint is not None
    assert result["controllers"]["publication_gate"]["action"] == "applied"

def test_domain_health_diagnostic_surfaces_runtime_efficiency_packet_and_gate_cache(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    quest_root = make_quest(tmp_path, "q001", status="running")
    evidence_sidecar = quest_root / ".ds" / "evidence_packets" / "run-1" / "bash_exec-large-log.json"
    dump_json(
        quest_root / ".ds" / "runs" / "run-1" / "telemetry.json",
        {
            "run_id": "run-1",
            "prompt_bytes": 32000,
            "tool_result_bytes_total": 90000,
            "compacted_tool_result_count": 3,
            "full_detail_tool_call_count": 1,
            "mcp_tool_call_count": 7,
            "model_inherited": True,
            "token_usage": {
                "input_tokens": 1000,
                "cached_input_tokens": 250,
                "output_tokens": 120,
            },
        },
    )
    dump_json(
        quest_root / ".ds" / "evidence_packets" / "run-1" / "index.json",
        {
            "items": [
                {
                    "tool_name": "bash_exec",
                    "detail": "compact",
                    "summary": "bash_exec: log_line_count=1200; key_blockers=1",
                    "payload_bytes": 64000,
                    "sidecar_path": str(evidence_sidecar),
                    "payload_sha256": "abc123",
                    "key_blockers": ["submission_minimal missing"],
                }
            ],
        },
    )
    dump_json(
        quest_root / ".ds" / "gate_cache" / "publication_gate.json",
        {
            "surface_id": "publication_gate",
            "input_fingerprint": "publication-gate-fp-1",
            "generated_at": "2026-04-28T10:00:00+00:00",
        },
    )

    result = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "clear",
                "blockers": [],
                "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            }
        },
        apply=False,
    )

    runtime_efficiency = result["runtime_efficiency"]
    assert runtime_efficiency["run_id"] == "run-1"
    assert runtime_efficiency["compacted_tool_result_count"] == 3
    assert runtime_efficiency["full_detail_tool_call_count"] == 1
    assert runtime_efficiency["latest_evidence_packets"][0]["summary"].startswith("bash_exec:")
    assert runtime_efficiency["gate_cache_surfaces"][0]["surface_id"] == "publication_gate"
    assert result["diagnostic_report_persistence"]["persisted"] is False
    assert not (quest_root / "artifacts" / "reports" / "domain_health_diagnostic").exists()

    refreshed = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "clear",
                "blockers": [],
                "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            }
        },
        apply=False,
        persist_diagnostic_reports=True,
    )
    assert refreshed["diagnostic_report_persistence"]["persisted"] is True
    latest_markdown = (quest_root / "artifacts" / "reports" / "domain_health_diagnostic" / "latest.md").read_text(
        encoding="utf-8"
    )
    assert "## Runtime Efficiency" in latest_markdown
    assert "上下文效率" in latest_markdown
    assert "publication_gate" in latest_markdown

def test_domain_health_diagnostic_preserves_publication_supervisor_summary(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    quest_root = make_quest(tmp_path, "q001", status="running")

    result = module.run_domain_health_diagnostic_for_quest(
        quest_root=quest_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "blocked",
                "blockers": ["missing_post_main_publishability_gate"],
                "allow_write": False,
                "missing_non_scalar_deliverables": [],
                "submission_minimal_present": True,
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
                "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
                "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            }
        },
        apply=False,
    )

    controller = result["controllers"]["publication_gate"]
    assert controller["supervisor_phase"] == "publishability_gate_blocked"
    assert controller["phase_owner"] == "publication_gate"
    assert controller["upstream_scientific_anchor_ready"] is True
    assert controller["bundle_tasks_downstream_only"] is True
    assert controller["current_required_action"] == "return_to_publishability_gate"
    assert controller["deferred_downstream_actions"] == []
    assert "downstream-only" in controller["controller_stage_note"]
