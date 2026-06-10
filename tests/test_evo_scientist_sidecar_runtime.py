from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_evo_scientist_sidecar_writer_records_refs_only_observation(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.evo_scientist_sidecar_refs")
    study_root = tmp_path / "study"
    study_root.mkdir()

    result = module.write_evo_scientist_sidecar_observation(
        study_root=study_root,
        event={
            "event_kind": "current_owner_delta_materialized",
            "source": "unit-test",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "current_owner_delta_ref": "control/projection/current_owner_delta.json",
            "owner_policy_ref": "agent/stages/stage_route_contract.yaml",
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "next_owner": "MedAutoScience",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "manuscript_story_repair",
                "source_ref": "artifacts/runtime/owner_route/latest.json",
            },
        },
        apply=True,
    )

    assert result["status"] == "recorded"
    assert result["write_status"] == "written"
    assert result["body_included"] is False
    assert result["counts_as_paper_progress"] is False
    assert result["counts_as_owner_answer"] is False
    assert result["can_close_stage"] is False
    assert result["nonblocking_contract"] == {
        "mainline_waits_for_sidecar": False,
        "failure_blocks_current_owner_action": False,
        "timeout_blocks_current_owner_action": False,
        "budget_exhaustion_blocks_current_owner_action": False,
        "sidecar_completion_required_for_dispatch": False,
        "sidecar_completion_required_for_quality_gate": False,
        "sidecar_completion_required_for_artifact_mutation": False,
    }
    assert result["authority_boundary"]["can_write_publication_eval"] is False
    assert result["authority_boundary"]["can_write_controller_decisions"] is False
    assert result["authority_boundary"]["can_write_owner_receipt"] is False
    assert result["authority_boundary"]["can_write_typed_blocker"] is False
    assert set(result["outputs"]) == {
        "tool_affordance_ref",
        "observation_memory_ref",
        "failed_path_memory_ref",
        "reviewer_briefing_ref",
        "route_hint_ref",
        "stop_loss_candidate_ref",
    }
    assert "artifacts/publication_eval/latest.json" in result["forbidden_write_surfaces"]
    assert "artifacts/controller_decisions/latest.json" in result["forbidden_write_surfaces"]

    observation_path = study_root / result["observation_ref"]
    latest_path = study_root / "artifacts" / "runtime" / "evo_scientist_sidecar" / "latest.json"
    assert observation_path.is_file()
    assert latest_path.is_file()
    latest = json.loads(latest_path.read_text(encoding="utf-8"))
    assert latest["event_id"] == result["event_id"]
    assert latest["payload_role"] == "refs_only_observation"

    projection = module.read_latest_evo_scientist_sidecar_projection(study_root=study_root)
    assert projection["status"] == "available"
    assert projection["observation"]["event_id"] == result["event_id"]


def test_evo_scientist_sidecar_writer_is_event_fingerprint_idempotent(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.evo_scientist_sidecar_refs")
    study_root = tmp_path / "study"
    study_root.mkdir()
    event = {
        "event_kind": "current_owner_delta_materialized",
        "current_owner_delta_ref": "control/projection/current_owner_delta.json",
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "next_owner": "MedAutoScience",
            "action_type": "run_quality_repair_batch",
        },
    }

    first = module.write_evo_scientist_sidecar_observation(
        study_root=study_root,
        event=event,
        apply=True,
    )
    second = module.write_evo_scientist_sidecar_observation(
        study_root=study_root,
        event=event,
        apply=True,
    )

    assert first["event_id"] == second["event_id"]
    assert first["observation_ref"] == second["observation_ref"]
    assert second["write_status"] == "existing_ref_reused"
    assert second["written_refs"] == []
    observations = list(
        (study_root / "artifacts" / "runtime" / "evo_scientist_sidecar" / "observations").glob(
            "*.json"
        )
    )
    assert len(observations) == 1


def test_evo_scientist_sidecar_observes_current_owner_payload(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.evo_scientist_sidecar_refs")
    study_root = tmp_path / "study"
    study_root.mkdir()

    result = module.observe_current_owner_payload(
        study_root=study_root,
        progress_payload={
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "active_run_id": "run-001",
            "stage_kernel_projection": {
                "refs": {
                    "current_owner_delta_ref": "control/projection/current_owner_delta.json",
                }
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "next_owner": "MedAutoScience",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "manuscript_story_repair",
                "work_unit_fingerprint": "sha256:abc",
                "source_ref": "artifacts/runtime/owner_route/latest.json",
            },
            "current_work_unit": {
                "work_unit_id": "manuscript_story_repair",
                "work_unit_fingerprint": "sha256:abc",
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "next_owner": "MedAutoScience",
            },
        },
        apply=True,
    )

    assert result["status"] == "recorded"
    assert result["event_kind"] == "current_owner_delta_materialized"
    assert result["source"] == "study_progress.materialize_read_model_artifacts"
    assert result["current_owner_delta_ref"] == "control/projection/current_owner_delta.json"
    assert result["current_owner_action_ref"] == "artifacts/runtime/owner_route/latest.json"
    assert result["current_owner_summary"] == {
        "next_owner": "MedAutoScience",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "manuscript_story_repair",
        "work_unit_fingerprint": "sha256:abc",
        "envelope_state_kind": "executable_owner_action",
        "status": "ready",
        "source": None,
    }


def test_evo_scientist_sidecar_dry_run_and_skipped_inputs_do_not_write(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.runtime_protocol.evo_scientist_sidecar_refs")
    study_root = tmp_path / "study"
    study_root.mkdir()

    dry_run = module.write_evo_scientist_sidecar_observation(
        study_root=study_root,
        event={"event_kind": "executor_turn_completed", "receipt_or_typed_blocker_ref": "r1"},
        apply=False,
    )
    assert dry_run["status"] == "recorded"
    assert dry_run["write_status"] == "dry_run_no_write"
    assert dry_run["written_refs"] == []
    assert not (study_root / dry_run["observation_ref"]).exists()

    skipped = module.write_evo_scientist_sidecar_observation(
        study_root=study_root,
        event={"event_kind": "executor_turn_completed"},
        apply=True,
    )
    assert skipped["status"] == "skipped"
    assert skipped["write_status"] == "skipped_no_write"
    assert skipped["nonblocking_contract"]["failure_blocks_current_owner_action"] is False
    assert not (study_root / "artifacts" / "runtime" / "evo_scientist_sidecar").exists()


def test_evo_scientist_sidecar_cli_observe_and_read_latest(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    study_root = tmp_path / "study"
    study_root.mkdir()

    event = {
        "event_kind": "receipt_or_typed_blocker_recorded",
        "receipt_or_typed_blocker_ref": "artifacts/stage_outputs/typed_blocker.json",
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "next_owner": "MedAutoScience",
            "action_type": "complete_medical_paper_readiness_surface",
        },
    }
    exit_code = cli.main(
        [
            "evo-scientist-sidecar",
            "observe",
            "--study-root",
            str(study_root),
            "--event-json",
            json.dumps(event),
            "--apply",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "recorded"
    assert payload["write_status"] == "written"

    exit_code = cli.main(
        [
            "evo-scientist-sidecar",
            "read-latest",
            "--study-root",
            str(study_root),
        ]
    )
    captured = capsys.readouterr()
    latest = json.loads(captured.out)
    assert exit_code == 0
    assert latest["status"] == "available"
    assert latest["observation"]["event_id"] == payload["event_id"]


def test_evo_scientist_sidecar_refs_enter_refs_only_state_index(tmp_path: Path) -> None:
    sidecar = importlib.import_module("med_autoscience.runtime_protocol.evo_scientist_sidecar_refs")
    state_index = importlib.import_module("med_autoscience.runtime_protocol.refs_only_state_index_pilot")
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    quest_root = workspace_root / "runtime" / "quests" / "quest-001"
    study_root.mkdir(parents=True)
    quest_root.mkdir(parents=True)
    (quest_root / "artifacts" / "runtime" / "state").mkdir(parents=True)
    (quest_root / "artifacts" / "runtime" / "state" / "runtime_state.json").write_text(
        json.dumps({"quest_id": "quest-001", "status": "running"}, indent=2) + "\n",
        encoding="utf-8",
    )
    sidecar.write_evo_scientist_sidecar_observation(
        study_root=study_root,
        event={
            "event_kind": "current_owner_delta_materialized",
            "current_owner_delta_ref": "control/projection/current_owner_delta.json",
        },
        apply=True,
    )

    result = state_index.rebuild_refs_only_state_index(
        workspace_root=workspace_root,
        study_root=study_root,
        quest_root=quest_root,
    )

    assert result["family_counts"]["evo_scientist_sidecar_ref"] == 2
    assert result["authority_boundary"]["body_included"] is False
