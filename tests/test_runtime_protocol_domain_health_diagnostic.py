from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_load_and_save_domain_health_diagnostic_state_round_trip(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.domain_health_diagnostic")
    quest_root = tmp_path / "runtime" / "quests" / "q001"

    initial = module.load_domain_health_diagnostic_state(quest_root)
    assert initial == module.DomainHealthDiagnosticState(
        schema_version=1,
        updated_at=None,
        controllers={},
    )

    module.save_domain_health_diagnostic_state(
        quest_root,
        module.DomainHealthDiagnosticState(
            schema_version=1,
            updated_at="2026-04-02T12:00:00+00:00",
            controllers={
                "publication_gate": module.DomainHealthDiagnosticControllerState(
                    last_seen_fingerprint="fp-1",
                    last_applied_fingerprint=None,
                    last_applied_at=None,
                    last_status=None,
                    last_suppression_reason=None,
                )
            },
        ),
    )

    stored = module.load_domain_health_diagnostic_state(quest_root)
    assert stored == module.DomainHealthDiagnosticState(
        schema_version=1,
        updated_at="2026-04-02T12:00:00+00:00",
        controllers={
            "publication_gate": module.DomainHealthDiagnosticControllerState(
                last_seen_fingerprint="fp-1",
                last_applied_fingerprint=None,
                last_applied_at=None,
                last_status=None,
                last_suppression_reason=None,
            )
        },
    )


def test_write_domain_health_diagnostic_report_uses_runtime_protocol_paths(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.domain_health_diagnostic")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    report = {
        "scanned_at": "2026-04-02T12:00:00+00:00",
        "quest_root": str(quest_root),
        "quest_status": "running",
    }

    json_path, md_path = module.write_domain_health_diagnostic_report(
        quest_root=quest_root,
        report=report,
        markdown="# Domain Health Diagnostic Report\n",
    )

    assert json_path == quest_root / "artifacts" / "reports" / "domain_health_diagnostic" / "2026-04-02T120000Z.json"
    assert md_path == quest_root / "artifacts" / "reports" / "domain_health_diagnostic" / "2026-04-02T120000Z.md"
    assert json.loads(json_path.read_text(encoding="utf-8"))["quest_status"] == "running"
    assert md_path.read_text(encoding="utf-8") == "# Domain Health Diagnostic Report\n"


def test_plan_controller_intervention_applies_once_and_persists_fingerprint() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.domain_health_diagnostic")

    result = module.plan_controller_intervention(
        previous_controller_state=module.DomainHealthDiagnosticControllerState(),
        dry_run_result={"status": "blocked", "blockers": ["b1"]},
        fingerprint="fp-1",
        apply=True,
        scanned_at="2026-04-02T12:00:00+00:00",
        intervention_statuses={"blocked"},
    )

    assert result == module.DomainHealthDiagnosticInterventionPlan(
        action=module.DomainHealthDiagnosticControllerAction.APPLIED,
        should_apply=True,
        suppression_reason=None,
        controller_state=module.DomainHealthDiagnosticControllerState(
            last_seen_fingerprint="fp-1",
            last_applied_fingerprint="fp-1",
            last_applied_at="2026-04-02T12:00:00+00:00",
            last_status="blocked",
            last_suppression_reason=None,
        ),
    )


def test_plan_controller_intervention_suppresses_duplicate_fingerprint() -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.domain_health_diagnostic")

    result = module.plan_controller_intervention(
        previous_controller_state=module.DomainHealthDiagnosticControllerState(
            last_seen_fingerprint=None,
            last_applied_fingerprint="fp-1",
            last_applied_at="earlier",
            last_status=None,
            last_suppression_reason=None,
        ),
        dry_run_result={"status": "blocked", "blockers": ["b1"]},
        fingerprint="fp-1",
        apply=True,
        scanned_at="2026-04-02T12:00:00+00:00",
        intervention_statuses={"blocked"},
    )

    assert result == module.DomainHealthDiagnosticInterventionPlan(
        action=module.DomainHealthDiagnosticControllerAction.SUPPRESSED,
        should_apply=False,
        suppression_reason="duplicate_fingerprint",
        controller_state=module.DomainHealthDiagnosticControllerState(
            last_seen_fingerprint="fp-1",
            last_applied_fingerprint="fp-1",
            last_applied_at="earlier",
            last_status="blocked",
            last_suppression_reason="duplicate_fingerprint",
        ),
    )


def test_domain_health_diagnostic_uses_shared_report_store_helpers(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.domain_health_diagnostic")
    quest_root = tmp_path / "runtime" / "quests" / "q001"
    seen: dict[str, object] = {}

    def fake_load_domain_health_diagnostic_state(path: Path) -> dict[str, object]:
        seen["loaded"] = str(path)
        return {"schema_version": 1, "updated_at": "2026-04-02T12:00:00+00:00", "controllers": {}}

    def fake_save_domain_health_diagnostic_state(path: Path, payload: dict[str, object]) -> None:
        seen["saved"] = (str(path), payload)

    def fake_write_timestamped_report(
        *,
        quest_root: Path,
        report_group: str,
        timestamp: str,
        report: dict[str, object],
        markdown: str,
    ) -> tuple[Path, Path]:
        seen["reported"] = (str(quest_root), report_group, timestamp, report, markdown)
        return quest_root / "artifacts" / "reports" / report_group / "latest.json", quest_root / "artifacts" / "reports" / report_group / "latest.md"

    monkeypatch.setattr(module.report_store, "load_domain_health_diagnostic_state", fake_load_domain_health_diagnostic_state)
    monkeypatch.setattr(module.report_store, "save_domain_health_diagnostic_state", fake_save_domain_health_diagnostic_state)
    monkeypatch.setattr(module.report_store, "write_timestamped_report", fake_write_timestamped_report)

    loaded = module.load_domain_health_diagnostic_state(quest_root)
    module.save_domain_health_diagnostic_state(
        quest_root,
        module.DomainHealthDiagnosticState(
            schema_version=1,
            updated_at="2026-04-02T12:00:00+00:00",
            controllers={},
        ),
    )
    json_path, md_path = module.write_domain_health_diagnostic_report(
        quest_root=quest_root,
        report={"scanned_at": "2026-04-02T12:00:00+00:00", "quest_status": "running"},
        markdown="# Domain Health Diagnostic Report\n",
    )

    assert loaded == module.DomainHealthDiagnosticState(
        schema_version=1,
        updated_at="2026-04-02T12:00:00+00:00",
        controllers={},
    )
    assert seen["loaded"] == str(quest_root)
    assert seen["saved"] == (
        str(quest_root),
        {"schema_version": 1, "updated_at": "2026-04-02T12:00:00+00:00", "controllers": {}},
    )
    assert seen["reported"] == (
        str(quest_root),
        "domain_health_diagnostic",
        "2026-04-02T12:00:00+00:00",
        {"scanned_at": "2026-04-02T12:00:00+00:00", "quest_status": "running"},
        "# Domain Health Diagnostic Report\n",
    )
    assert json_path.name == "latest.json"
    assert md_path.name == "latest.md"
