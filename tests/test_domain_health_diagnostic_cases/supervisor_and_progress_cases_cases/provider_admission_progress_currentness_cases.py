from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def _currentness_basis(
    *,
    work_unit_id: str,
    fingerprint: str,
    source_eval_id: str = "publication-eval::current",
) -> dict[str, str]:
    return {
        "truth_epoch": f"truth::{fingerprint}",
        "runtime_health_epoch": f"runtime-health::{fingerprint}",
        "source_eval_id": source_eval_id,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
    }


def test_runtime_scan_preserves_fresh_progress_provider_admission_candidate(
    tmp_path: Path,
    monkeypatch,
) -> None:
    runtime_scan = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.runtime_scan"
    )
    study_progress = importlib.import_module("med_autoscience.controllers.study_progress")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = helpers.write_study(profile.workspace_root, study_id, quest_id=study_id)
    work_unit_id = "publication_gate_replay"
    fingerprint = "sha256:current-progress-provider-admission"
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "next_executable_owner": "gate_clearing_batch",
        "dispatch_path": str(dispatch_path),
        "provider_attempt_or_lease_required": True,
        "owner_route_current": True,
        "currentness_basis": _currentness_basis(
            work_unit_id=work_unit_id,
            fingerprint=fingerprint,
        ),
    }

    monkeypatch.setattr(
        study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": work_unit_id,
            },
            "current_executable_owner_action": {
                "status": "ready",
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
            "provider_admission_candidates": [candidate],
            "provider_admission_pending_count": 1,
            "paper_recovery_state": {
                "phase": "admission_pending",
                "next_safe_action": {
                    "kind": "admit_provider_attempt",
                    "provider_admission_allowed": True,
                },
            },
        },
    )

    result = runtime_scan._provider_admission_candidates_for_status(
        profile=profile,
        study_root=study_root,
        status_payload={"study_id": study_id, "quest_id": study_id},
        refresh_currentness=True,
    )

    assert result == [candidate]
