from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


MODULE_NAME = "med_autoscience.controller_confirmation_summary"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_controller_decision(
    study_root: Path,
    *,
    requires_human_confirmation: bool,
    action_type: str = "stop_runtime",
) -> Path:
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    _write_json(
        decision_path,
        {
            "schema_version": 1,
            "decision_id": "study-decision::001-risk::quest-001::stop_loss::2026-04-20T03:00:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-20T03:00:00+00:00",
            "decision_type": "stop_loss",
            "charter_ref": {
                "charter_id": "charter::001-risk::v1",
                "artifact_path": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            },
            "runtime_escalation_ref": {
                "record_id": "runtime-escalation::001-risk::quest-001::publishability_gate_blocked::2026-04-20T02:58:00+00:00",
                "artifact_path": str(study_root / "ops" / "quest-001" / "runtime_escalation_record.json"),
                "summary_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            },
            "publication_eval_ref": {
                "eval_id": "publication-eval::001-risk::quest-001::2026-04-20T02:59:00+00:00",
                "artifact_path": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
            },
            "requires_human_confirmation": requires_human_confirmation,
            "controller_actions": [
                {
                    "action_type": action_type,
                    "payload_ref": str(decision_path),
                }
            ],
            "reason": "当前控制面建议需要医生或 PI 明确确认。",
        },
    )
    return decision_path


def test_resolve_controller_confirmation_summary_ref_defaults_to_stable_artifact(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"

    resolved = module.resolve_controller_confirmation_summary_ref(study_root=study_root)

    assert resolved == (study_root / "artifacts" / "controller" / "controller_confirmation_summary.json").resolve()


def test_resolve_controller_confirmation_summary_ref_rejects_non_stable_paths(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    runtime_ref = study_root / "runtime" / "controller_confirmation_summary.json"

    with pytest.raises(ValueError, match="stable controller artifact"):
        module.resolve_controller_confirmation_summary_ref(study_root=study_root, ref=runtime_ref)


def test_materialize_controller_confirmation_summary_writes_pending_surface(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    decision_path = _write_controller_decision(study_root, requires_human_confirmation=True)

    written_ref = module.materialize_controller_confirmation_summary(study_root=study_root)
    payload = module.read_controller_confirmation_summary(study_root=study_root)

    assert written_ref == {
        "summary_id": "controller-confirmation::001-risk::study-decision::001-risk::quest-001::stop_loss::2026-04-20T03:00:00+00:00",
        "artifact_path": str(
            (study_root / "artifacts" / "controller" / "controller_confirmation_summary.json").resolve()
        ),
    }
    assert payload["status"] == "pending"
    assert payload["decision_ref"] == {
        "decision_id": "study-decision::001-risk::quest-001::stop_loss::2026-04-20T03:00:00+00:00",
        "artifact_path": str(decision_path.resolve()),
    }
    assert payload["allowed_responses"] == ["approve", "request_changes", "reject"]
    assert payload["controller_action_types"] == ["stop_runtime"]
    assert payload["question_for_user"] == "请确认是否允许 MAS 停止当前研究运行。"
    assert payload["next_action_if_approved"] == "停止当前研究运行"


def test_materialize_controller_confirmation_summary_removes_stale_surface_when_gate_clears(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_controller_decision(study_root, requires_human_confirmation=True)
    summary_path = study_root / "artifacts" / "controller" / "controller_confirmation_summary.json"

    assert module.materialize_controller_confirmation_summary(study_root=study_root) is not None
    assert summary_path.exists()

    _write_controller_decision(study_root, requires_human_confirmation=False, action_type="ensure_study_runtime")

    written_ref = module.materialize_controller_confirmation_summary(study_root=study_root)

    assert written_ref is None
    assert not summary_path.exists()


def test_materialize_controller_confirmation_summary_rejects_autonomous_scientific_gate(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_controller_decision(study_root, requires_human_confirmation=True, action_type="ensure_study_runtime")
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    payload = json.loads(decision_path.read_text(encoding="utf-8"))
    payload["decision_type"] = "continue_same_line"
    _write_json(decision_path, payload)

    with pytest.raises(ValueError, match="major direction pivots"):
        module.materialize_controller_confirmation_summary(study_root=study_root)

    assert not (study_root / "artifacts" / "controller" / "controller_confirmation_summary.json").exists()
