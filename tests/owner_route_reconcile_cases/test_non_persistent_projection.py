from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import make_profile, write_study


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_scan_domain_routes_can_project_without_overwriting_workspace_latest(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    monkeypatch.setenv("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN", "gaofeng21cn")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id="quest-dpcc")
    quest_root = profile.runtime_root / "quest-dpcc"
    latest_path = profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        latest_path,
        {
            "surface": "opl_current_control_state_handoff",
            "generated_at": "2026-05-05T00:00:00+00:00",
            "studies": [
                {"study_id": "001-dm-cvd-mortality-risk"},
                {"study_id": study_id},
            ],
            "action_queue": [{"study_id": "001-dm-cvd-mortality-risk", "action_id": "existing"}],
        },
    )
    before = latest_path.read_text(encoding="utf-8")

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": "quest-dpcc",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "decision": "blocked",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "attempt_state": "escalated",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
            "publication_eval": {
                "assessment_provenance": {"owner": "mechanical_projection", "ai_reviewer_required": True},
            },
        },
    )
    monkeypatch.setattr(
        module.study_progress,
        "read_study_progress",
        lambda **_: {
            "study_id": study_id,
            "paper_stage": "publication_supervision",
            "supervision": {"active_run_id": None, "health_status": "recovering"},
            "ai_repair_lifecycle": {
                "state": "external_supervisor_required",
                "blocked_reason": "runtime_recovery_not_authorized",
                "external_supervisor_required": True,
            },
        },
    )

    result = module.scan_domain_routes(
        profile=profile,
        study_ids=(study_id,),
        apply_safe_actions=True,
        persist_surfaces=False,
    )

    assert result["studies"][0]["study_id"] == study_id
    assert latest_path.read_text(encoding="utf-8") == before
    assert not (profile.workspace_root / "artifacts" / "supervision" / "hourly" / "history.jsonl").exists()


def test_scan_domain_routes_rejects_unknown_study_id_before_reading_status(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.owner_route_reconcile")
    profile = make_profile(tmp_path)
    write_study(profile.workspace_root, "001-dm-cvd-mortality-risk", quest_id="quest-dm001")
    write_study(profile.workspace_root, "002-dm-china-us-mortality-attribution", quest_id="quest-dm002")

    def fail_if_called(**_: object) -> dict[str, object]:
        raise AssertionError("unknown study ids must be rejected before runtime status is read")

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", fail_if_called)
    monkeypatch.setattr(module.study_progress, "read_study_progress", fail_if_called)

    with pytest.raises(ValueError, match="Unknown supervisor study_id: DM002"):
        module.scan_domain_routes(
            profile=profile,
            study_ids=("DM002",),
            apply_safe_actions=True,
            persist_surfaces=False,
        )
