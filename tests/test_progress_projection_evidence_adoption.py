from __future__ import annotations

import importlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from tests.study_runtime_test_helpers import (
    _clear_readiness_report,
    make_profile,
    write_study,
    write_text,
)


STUDY_ID = "001-risk"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _setup_study(tmp_path: Path):
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        STUDY_ID,
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="Clinical survival framing is fixed.",
        paper_urls=["https://example.org/paper-1"],
        journal_shortlist=["BMC Medicine"],
        minimum_sci_ready_evidence_package=["external_validation"],
    )
    quest_root = profile.runtime_root / STUDY_ID
    write_text(quest_root / "quest.yaml", f"quest_id: {STUDY_ID}\nstudy_id: {STUDY_ID}\n")
    _write_json(
        profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json",
        {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "authority": "observability_only",
            "studies": [{
                "study_id": STUDY_ID,
                "quest_id": STUDY_ID,
                "active_run_id": "opl-stage-attempt://sat-evidence-adoption",
                "running_provider_attempt": True,
                "runtime_health": {"runtime_liveness_status": "live"},
            }],
        },
    )
    return profile, study_root, quest_root


def _patch_readiness(module, monkeypatch, profile) -> None:
    monkeypatch.setattr(
        module,
        "inspect_workspace_contracts",
        lambda profile: {
            "overall_ready": True,
            "runtime_contract": {"ready": True},
            "launcher_contract": {"ready": True},
            "behavior_gate": {"ready": True, "phase_25_ready": True},
        },
    )
    monkeypatch.setattr(
        module.startup_data_readiness_controller,
        "startup_data_readiness",
        lambda *, workspace_root: _clear_readiness_report(workspace_root, STUDY_ID),
    )


def test_read_only_study_progress_does_not_materialize_authority_or_status_artifacts(
    monkeypatch,
    tmp_path: Path,
) -> None:
    status_module = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    progress_module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
    profile, study_root, quest_root = _setup_study(tmp_path)
    _write_json(
        quest_root / "artifacts" / "reports" / "domain_diagnostic_report" / "latest.json",
        {"controllers": {"publication_gate": {"report_json": str(
            quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"
        )}}},
    )
    _write_json(
        quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json",
        {
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "quest_id": STUDY_ID,
            "study_id": STUDY_ID,
            "paper_root": str(study_root / "paper"),
            "status": "blocked",
            "allow_write": False,
            "recommended_action": "return_to_controller",
            "blockers": ["medical_publication_surface_blocked"],
            "supervisor_phase": "publishability_gate_blocked",
            "current_required_action": "return_to_publishability_gate",
        },
    )
    forbidden = [
        study_root / "artifacts" / "publication_eval" / "latest.json",
        study_root / "artifacts" / "runtime" / "runtime_status_summary.json",
        study_root / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json",
        study_root / "artifacts" / "controller" / "controller_summary.json",
        study_root / "artifacts" / "controller" / "study_charter.json",
        study_root / "artifacts" / "medical_paper" / "readiness.json",
        study_root / "artifacts" / "eval_hygiene" / "promotion_gate" / "latest.json",
        study_root / "artifacts" / "eval_hygiene" / "runtime_escalation_context" / "latest.json",
    ]
    for path in forbidden:
        path.unlink(missing_ok=True)
    _patch_readiness(status_module, monkeypatch, profile)

    with pytest.raises(
        FileNotFoundError,
        match="requires an OPL runtime owner handoff ref",
    ):
        progress_module.read_study_progress(
            profile=profile,
            study_id=STUDY_ID,
            sync_runtime_summary=False,
        )

    assert not any(path.exists() for path in forbidden)
