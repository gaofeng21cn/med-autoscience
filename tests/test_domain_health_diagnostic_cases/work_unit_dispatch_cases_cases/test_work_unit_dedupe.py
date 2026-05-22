from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_work_unit_dedupe_does_not_reuse_prior_upstream_unit_when_blocker_fingerprint_churns(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic_work_units")
    study_root = tmp_path / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json"
    latest_path.parent.mkdir(parents=True)
    latest_path.write_text(
        json.dumps(
            {
                "outcome": "dispatched",
                "work_unit_dispatch_key": "publication-blockers::old::analysis_claim_evidence_repair::run_gate_clearing_batch",
            }
        ),
        encoding="utf-8",
    )
    tick_request = {
        "work_unit_fingerprint": "publication-blockers::new",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }

    already_executed, dispatch_key = module.dispatch_already_executed(
        study_root=study_root,
        tick_request=tick_request,
    )

    assert already_executed is False
    assert dispatch_key == "publication-blockers::new::analysis_claim_evidence_repair::run_gate_clearing_batch"


def test_work_unit_dedupe_uses_ledger_when_latest_wakeup_was_overwritten_by_noop(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic_work_units")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    study_root = tmp_path / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json"
    latest_path.parent.mkdir(parents=True)
    latest_path.write_text(
        json.dumps({"outcome": "no_request"}),
        encoding="utf-8",
    )
    tick_request = {
        "work_unit_fingerprint": "publication-blockers::same",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }
    identity = module.identity_from_tick_request(
        study_id="001-risk",
        quest_id="quest-001",
        tick_request=tick_request,
    )
    ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="dispatched",
        payload={"source": "domain_health_diagnostic"},
        recorded_at="2026-04-28T00:00:00+00:00",
    )

    already_executed, dispatch_key = module.dispatch_already_executed(
        study_root=study_root,
        tick_request=tick_request,
    )

    assert already_executed is False
    assert dispatch_key == "publication-blockers::same::analysis_claim_evidence_repair::run_gate_clearing_batch"


def test_work_unit_dedupe_requires_attempt_result_not_bare_dispatch(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic_work_units")
    study_root = tmp_path / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json"
    latest_path.parent.mkdir(parents=True)
    latest_path.write_text(
        json.dumps(
            {
                "outcome": "dispatched",
                "work_unit_dispatch_key": "publication-blockers::same::analysis_claim_evidence_repair::run_gate_clearing_batch",
            }
        ),
        encoding="utf-8",
    )
    tick_request = {
        "work_unit_fingerprint": "publication-blockers::same",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }

    already_executed, dispatch_key = module.dispatch_already_executed(
        study_root=study_root,
        tick_request=tick_request,
    )

    assert already_executed is False
    assert dispatch_key == "publication-blockers::same::analysis_claim_evidence_repair::run_gate_clearing_batch"


def test_work_unit_dedupe_accepts_closed_attempt_result(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic_work_units")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    study_root = tmp_path / "studies" / "001-risk"
    tick_request = {
        "work_unit_fingerprint": "publication-blockers::same",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }
    identity = module.identity_from_tick_request(
        study_id="001-risk",
        quest_id="quest-001",
        tick_request=tick_request,
    )
    ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="closed",
        payload={"gate_replay_status": "clear"},
        recorded_at="2026-04-28T00:00:00+00:00",
    )

    already_executed, dispatch_key = module.dispatch_already_executed(
        study_root=study_root,
        tick_request=tick_request,
    )

    assert already_executed is True
    assert dispatch_key == "publication-blockers::same::analysis_claim_evidence_repair::run_gate_clearing_batch"


def test_work_unit_dedupe_rejects_closed_event_without_attempt_delta_or_gate_change(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic_work_units")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    study_root = tmp_path / "studies" / "001-risk"
    tick_request = {
        "work_unit_fingerprint": "publication-blockers::same",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }
    identity = module.identity_from_tick_request(
        study_id="001-risk",
        quest_id="quest-001",
        tick_request=tick_request,
    )
    ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="closed",
        payload={"dispatch_status": "executed"},
        recorded_at="2026-04-28T00:00:00+00:00",
    )

    already_executed, dispatch_key = module.dispatch_already_executed(
        study_root=study_root,
        tick_request=tick_request,
    )

    assert already_executed is False
    assert dispatch_key == "publication-blockers::same::analysis_claim_evidence_repair::run_gate_clearing_batch"


def test_work_unit_dedupe_accepts_closed_event_with_attempt_record(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic_work_units")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    study_root = tmp_path / "studies" / "001-risk"
    tick_request = {
        "work_unit_fingerprint": "publication-blockers::same",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }
    identity = module.identity_from_tick_request(
        study_id="001-risk",
        quest_id="quest-001",
        tick_request=tick_request,
    )
    ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="closed",
        payload={
            "dispatch_status": "executed",
            "attempt_record": {
                "attempt_state": "released",
                "attempt_count": 1,
                "work_unit_id": "analysis_claim_evidence_repair",
            },
        },
        recorded_at="2026-04-28T00:00:00+00:00",
    )

    already_executed, dispatch_key = module.dispatch_already_executed(
        study_root=study_root,
        tick_request=tick_request,
    )

    assert already_executed is True
    assert dispatch_key == "publication-blockers::same::analysis_claim_evidence_repair::run_gate_clearing_batch"


def test_work_unit_redrive_budget_resets_after_evidenced_close(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic_work_units")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    study_root = tmp_path / "studies" / "001-risk"
    tick_request = {
        "work_unit_fingerprint": "publication-blockers::same",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }
    identity = module.identity_from_tick_request(
        study_id="001-risk",
        quest_id="quest-001",
        tick_request=tick_request,
    )
    for index in range(3):
        ledger.append_event(
            study_root=study_root,
            identity=identity,
            event_type="dispatched",
            payload={"source": "domain_health_diagnostic", "attempt": index + 1},
            recorded_at=f"2026-04-28T00:0{index}:00+00:00",
        )
    exhausted, dispatch_key, attempt_count = module.redrive_budget_exhausted(
        study_root=study_root,
        tick_request=tick_request,
    )
    assert exhausted is True
    assert dispatch_key == "publication-blockers::same::analysis_claim_evidence_repair::run_gate_clearing_batch"
    assert attempt_count == 3

    ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="closed",
        payload={"artifact_delta_ref": "artifacts/delta.json"},
        recorded_at="2026-04-28T00:03:00+00:00",
    )

    exhausted, _, attempt_count = module.redrive_budget_exhausted(
        study_root=study_root,
        tick_request=tick_request,
    )
    assert exhausted is False
    assert attempt_count == 0


def test_work_unit_dedupe_does_not_use_ledger_when_latest_inputs_changed(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic_work_units")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    study_root = tmp_path / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json"
    latest_path.parent.mkdir(parents=True)
    latest_path.write_text(
        json.dumps({"outcome": "no_request", "dispatch_cause": "input_changed"}),
        encoding="utf-8",
    )
    tick_request = {
        "work_unit_fingerprint": "publication-blockers::same",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }
    identity = module.identity_from_tick_request(
        study_id="001-risk",
        quest_id="quest-001",
        tick_request=tick_request,
    )
    ledger.append_event(
        study_root=study_root,
        identity=identity,
        event_type="dispatched",
        payload={"source": "domain_health_diagnostic"},
        recorded_at="2026-04-28T00:00:00+00:00",
    )

    already_executed, dispatch_key = module.dispatch_already_executed(
        study_root=study_root,
        tick_request=tick_request,
    )

    assert already_executed is False
    assert dispatch_key == "publication-blockers::same::analysis_claim_evidence_repair::run_gate_clearing_batch"


def test_work_unit_dedupe_does_not_use_ledger_for_prior_upstream_unit_when_fingerprint_churns(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic_work_units")
    ledger = importlib.import_module("med_autoscience.controllers.work_unit_ledger")
    study_root = tmp_path / "studies" / "001-risk"
    previous_request = {
        "work_unit_fingerprint": "publication-blockers::old",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }
    previous_identity = module.identity_from_tick_request(
        study_id="001-risk",
        quest_id="quest-001",
        tick_request=previous_request,
    )
    ledger.append_event(
        study_root=study_root,
        identity=previous_identity,
        event_type="dispatched",
        payload={"source": "domain_health_diagnostic"},
        recorded_at="2026-04-28T00:00:00+00:00",
    )
    tick_request = {
        "work_unit_fingerprint": "publication-blockers::new",
        "next_work_unit": {"unit_id": "analysis_claim_evidence_repair", "lane": "analysis-campaign"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }

    already_executed, dispatch_key = module.dispatch_already_executed(
        study_root=study_root,
        tick_request=tick_request,
    )

    assert already_executed is False
    assert dispatch_key == "publication-blockers::new::analysis_claim_evidence_repair::run_gate_clearing_batch"


def test_work_unit_dedupe_does_not_reuse_prior_delivery_unit_when_fingerprint_changes(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic_work_units")
    study_root = tmp_path / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "runtime" / "domain_health_diagnostic_wakeup" / "latest.json"
    latest_path.parent.mkdir(parents=True)
    latest_path.write_text(
        json.dumps(
            {
                "outcome": "dispatched",
                "work_unit_dispatch_key": "publication-blockers::old::submission_minimal_refresh::run_gate_clearing_batch",
            }
        ),
        encoding="utf-8",
    )
    tick_request = {
        "work_unit_fingerprint": "publication-blockers::new",
        "next_work_unit": {"unit_id": "submission_minimal_refresh"},
        "controller_actions": [{"action_type": "run_gate_clearing_batch"}],
    }

    already_executed, dispatch_key = module.dispatch_already_executed(
        study_root=study_root,
        tick_request=tick_request,
    )

    assert already_executed is False
    assert dispatch_key == "publication-blockers::new::submission_minimal_refresh::run_gate_clearing_batch"
