from __future__ import annotations

import importlib
import json
from pathlib import Path

from .shared import write_profile


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_study_state_matrix_command_projects_macro_state_without_writing(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    studies_root = workspace_root / "studies"
    for study_id in ("001-dm", "002-dm"):
        study_root = studies_root / study_id
        study_root.mkdir(parents=True)
        (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")

    def fake_status(*, study_id, **_):
        if study_id == "002-dm":
            return {"study_id": study_id, "quest_status": "running", "active_run_id": "run-002"}
        return {
            "study_id": study_id,
            "quest_status": "paused",
            "active_run_id": None,
            "reason": "quest_waiting_for_submission_metadata",
            "auto_runtime_parked": {"parked": True, "parked_state": "external_metadata_pending"},
            "submission_metadata": {"missing_external_info": ["authors", "ethics", "funding"]},
            "study_truth_snapshot": {
                "truth_epoch": "truth-001",
                "source_signature": "source-001",
                "package_state": {"authority_state": "current"},
            },
        }

    monkeypatch.setattr(cli.study_runtime_router, "study_runtime_status", fake_status)

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["surface"] == "study_state_matrix"
    assert payload["counts"] == {"live": 1, "parked": 1}
    assert payload["studies"][0]["study_id"] == "001-dm"
    assert payload["studies"][0]["study_macro_state"]["user_next"] == "submit_info"
    assert payload["studies"][0]["domain_transition"]["decision_type"] == "human_gate"
    assert payload["studies"][1]["study_macro_state"]["writer_state"] == "live"
    assert payload["studies"][1]["active_run_id"] == "run-002"
    assert payload["studies"][1]["domain_transition"]["decision_type"] == "active_runtime_watch"
    assert payload["domain_transition_table"]["counts"] == {"human_gate": 1, "active_runtime_watch": 1}


def test_study_state_matrix_markdown_uses_short_macro_status(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / "004-invasive"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 004-invasive\n", encoding="utf-8")

    monkeypatch.setattr(
        cli.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "004-invasive",
            "quest_status": "paused",
            "active_run_id": None,
            "reason": "publishability_stop_loss_recommended",
            "study_truth_snapshot": {
                "quality_state": {"state": "stop_loss_recommended"},
                "package_state": {"authority_state": "current"},
            },
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "markdown"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "| 004-invasive | parked | none | stop_loss |" in captured.out
    assert "| 004-invasive | stop_loss | stop | stop_loss_handoff | stop_runtime | med-autoscience | stop_loss_active |" in captured.out
    assert "publishability_stop_loss_recommended" not in captured.out


def test_study_state_matrix_marks_stop_line_milestone_package_without_reopening_quality_gate(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / "004-dpcc"
    package_root = study_root / "manuscript" / "current_package"
    (package_root / "figures").mkdir(parents=True)
    (package_root / "tables").mkdir()
    (study_root / "study.yaml").write_text("study_id: 004-dpcc\n", encoding="utf-8")
    for path in (
        package_root / "manuscript.docx",
        package_root / "paper.pdf",
        package_root / "figures" / "Figure1.png",
        package_root / "tables" / "Table1.csv",
        study_root / "manuscript" / "current_package.zip",
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder\n", encoding="utf-8")
    (package_root / "SUBMISSION_TODO.md").write_text(
        "# Submission TODO\n\nPending items:\n- Authors: pending\n- Ethics: pending\n- Funding: pending\n",
        encoding="utf-8",
    )
    (package_root / "submission_manifest.json").write_text(
        json.dumps(
            {
                "figures": [{"figure_id": "F1"}],
                "tables": [{"table_id": "T1"}],
                "surface_qc": {"status": "pass", "failures": []},
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        cli.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "004-dpcc",
            "study_root": str(study_root),
            "quest_status": "paused",
            "active_run_id": None,
            "reason": "quest_waiting_for_explicit_wakeup_after_manual_hold",
            "study_truth_snapshot": {
                "quality_state": {"state": "user_stopped"},
                "package_state": {"authority_state": "not_observed"},
            },
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    study = json.loads(captured.out)["studies"][0]

    assert exit_code == 0
    assert study["study_macro_state"]["writer_state"] == "parked"
    assert study["study_macro_state"]["reason"] == "user_stop"
    assert study["study_macro_state"]["details"]["package_delivered"] is True
    assert study["delivered_package"]["authority_role"] == "user_visible_milestone_package_not_quality_authority"
    assert study["domain_transition"]["decision_type"] == "stop_loss"
    assert study["domain_transition"]["guard_boundary"]["opl_generic_runner_may_resume"] is False


def test_study_state_matrix_top_active_run_uses_macro_truth_when_status_top_level_is_empty(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / "002-dm"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 002-dm\n", encoding="utf-8")

    monkeypatch.setattr(
        cli.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "002-dm",
            "study_root": str(study_root),
            "quest_status": "active",
            "active_run_id": None,
            "study_truth_snapshot": {
                "active_run_id": "run-from-truth",
                "execution_owner": {"active_run_id": "run-from-truth"},
            },
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    study = json.loads(captured.out)["studies"][0]

    assert exit_code == 0
    assert study["active_run_id"] == "run-from-truth"
    assert study["study_macro_state"]["writer_state"] == "live"
    assert study["domain_transition"]["decision_type"] == "active_runtime_watch"
    assert study["domain_transition"]["controller_action"] == "runtime_watch"


def test_study_state_matrix_prefers_materialized_macro_state_surface(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / "004-dm"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 004-dm\n", encoding="utf-8")
    (study_root / "artifacts" / "runtime" / "study_macro_state").mkdir(parents=True)
    (study_root / "artifacts" / "runtime" / "study_macro_state" / "latest.json").write_text(
        json.dumps(
            {
                "surface": "study_macro_state",
                "schema_version": 1,
                "study_id": "004-dm",
                "writer_state": "parked",
                "user_next": "none",
                "reason": "stop_loss",
                "details": {"reopen_allowed": False},
                "conditions": [{"type": "TerminalAbandon"}],
                "source_fingerprint": "macro-current",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        cli.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "004-dm",
            "study_root": str(study_root),
            "quest_status": "running",
            "active_run_id": "stale-run",
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    study = json.loads(captured.out)["studies"][0]

    assert exit_code == 0
    assert study["active_run_id"] is None
    assert study["study_macro_state"]["writer_state"] == "parked"
    assert study["study_macro_state"]["details"]["reopen_allowed"] is False
    assert study["domain_transition"]["decision_type"] == "stop_loss"


def test_study_state_matrix_projects_publication_gate_blocker_transition(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / "003-gate"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 003-gate\n", encoding="utf-8")
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "status": "blocked",
            "blockers": ["claim_specificity_gap"],
            "current_required_action": "complete_bundle_stage",
            "assessment_provenance": {"owner": "publication_gate"},
        },
    )

    monkeypatch.setattr(
        cli.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "003-gate",
            "study_root": str(study_root),
            "quest_status": "paused",
            "active_run_id": None,
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    transition = payload["studies"][0]["domain_transition"]

    assert exit_code == 0
    assert payload["domain_transition_table"]["surface"] == "study_domain_transition_table"
    assert payload["domain_transition_table"]["authority_boundary"]["owner"] == "MedAutoScience"
    assert payload["domain_transition_table"]["authority_boundary"]["runner_owner"] == "OPL Framework"
    assert transition["decision_type"] == "publication_gate_blocker"
    assert transition["route_target"] == "review"
    assert transition["next_work_unit"]["unit_id"] == "publication_gate_replay"
    assert transition["controller_action"] == "run_gate_clearing_batch"
    assert transition["owner"] == "publication_gate"
    assert transition["typed_blocker"]["blocker_id"] == "publication_gate_blocked"
    assert transition["typed_blocker"]["write_permitted"] is False
    assert transition["guard_boundary"]["runner_boundary"] == "mas_domain_read_model_only"
    assert transition["guard_boundary"]["can_execute_generic_state_machine"] is False


def test_study_state_matrix_projects_ai_reviewer_re_eval_transition(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / "002-review"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 002-review\n", encoding="utf-8")
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "domain_ready_verdict": "ai_reviewer_re_eval",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "source_kind": "publication_eval_ai_reviewer",
            },
        },
    )

    monkeypatch.setattr(
        cli.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "002-review",
            "study_root": str(study_root),
            "quest_status": "paused",
            "active_run_id": None,
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    transition = json.loads(captured.out)["studies"][0]["domain_transition"]

    assert exit_code == 0
    assert transition["decision_type"] == "ai_reviewer_re_eval"
    assert transition["route_target"] == "review"
    assert transition["next_work_unit"]["unit_id"] == "ai_reviewer_recheck"
    assert transition["controller_action"] == "return_to_ai_reviewer_workflow"
    assert transition["owner"] == "ai_reviewer"
    assert transition["typed_blocker"] is None
    assert transition["guard_boundary"]["required_owner_surface"] == "artifacts/publication_eval/latest.json"


def test_study_state_matrix_projects_artifact_delta_live_apply_transition(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_root = workspace_root / "studies" / "003-artifact"
    study_root.mkdir(parents=True)
    (study_root / "study.yaml").write_text("study_id: 003-artifact\n", encoding="utf-8")
    _write_json(
        study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json",
        {
            "canonical_artifact_delta": {"meaningful_artifact_delta": True},
            "progress_delta_candidate": True,
        },
    )

    monkeypatch.setattr(
        cli.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "study_id": "003-artifact",
            "study_root": str(study_root),
            "quest_status": "paused",
            "active_run_id": None,
        },
    )

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    transition = json.loads(captured.out)["studies"][0]["domain_transition"]

    assert exit_code == 0
    assert transition["decision_type"] == "artifact_delta_live_apply"
    assert transition["route_target"] == "finalize"
    assert transition["next_work_unit"]["unit_id"] == "provider_hosted_guarded_apply"
    assert transition["controller_action"] == "paper_autonomy_guarded_apply"
    assert transition["owner"] == "med-autoscience"
    assert transition["typed_blocker"] is None
    assert transition["guard_boundary"]["mas_owner_apply_receipt_required"] is True


def test_study_state_matrix_fails_closed_for_human_gate_stop_loss_and_conflict_neighbors(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    study_ids = ("human-gate", "stop-loss", "truth-conflict")
    for study_id in study_ids:
        study_root = workspace_root / "studies" / study_id
        study_root.mkdir(parents=True)
        (study_root / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    _write_json(
        workspace_root / "studies" / "human-gate" / "artifacts" / "controller_decisions" / "latest.json",
        {
            "requires_human_confirmation": True,
            "family_human_gates": [{"gate_id": "confirm-target"}],
        },
    )
    _write_json(
        workspace_root / "studies" / "truth-conflict" / "artifacts" / "runtime" / "study_macro_state" / "latest.json",
        {
            "surface": "study_macro_state",
            "schema_version": 1,
            "study_id": "truth-conflict",
            "writer_state": "conflict",
            "user_next": "inspect",
            "reason": "truth_conflict",
            "details": {},
            "conditions": [],
        },
    )

    def fake_status(*, study_id, **_):
        study_root = workspace_root / "studies" / study_id
        if study_id == "stop-loss":
            return {
                "study_id": study_id,
                "study_root": str(study_root),
                "quest_status": "paused",
                "reason": "publishability_stop_loss_recommended",
                "study_truth_snapshot": {"quality_state": {"state": "stop_loss_recommended"}},
            }
        return {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_status": "paused",
            "active_run_id": None,
        }

    monkeypatch.setattr(cli.study_runtime_router, "study_runtime_status", fake_status)

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    rows = {row["study_id"]: row for row in json.loads(captured.out)["domain_transition_table"]["rows"]}

    assert exit_code == 0
    assert rows["human-gate"]["decision_type"] == "human_gate"
    assert rows["human-gate"]["controller_action"] == "wait_for_human_gate"
    assert rows["human-gate"]["typed_blocker"]["blocker_id"] == "human_gate_required"
    assert rows["human-gate"]["guard_boundary"]["opl_generic_runner_may_resume"] is False
    assert rows["stop-loss"]["decision_type"] == "stop_loss"
    assert rows["stop-loss"]["route_target"] == "stop"
    assert rows["stop-loss"]["controller_action"] == "stop_runtime"
    assert rows["stop-loss"]["guard_boundary"]["opl_generic_runner_may_resume"] is False
    assert rows["truth-conflict"]["decision_type"] == "fail_closed"
    assert rows["truth-conflict"]["route_target"] == "inspect"
    assert rows["truth-conflict"]["controller_action"] == "none"
    assert rows["truth-conflict"]["typed_blocker"]["blocker_id"] == "truth_conflict"
    assert rows["truth-conflict"]["typed_blocker"]["write_permitted"] is False


def test_study_state_matrix_projects_delivered_package_and_unclassified_fail_closed(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    delivered_root = workspace_root / "studies" / "package-ready"
    package_root = delivered_root / "manuscript" / "current_package"
    (package_root / "figures").mkdir(parents=True)
    (package_root / "tables").mkdir()
    (delivered_root / "study.yaml").write_text("study_id: package-ready\n", encoding="utf-8")
    for path in (
        package_root / "manuscript.docx",
        package_root / "paper.pdf",
        package_root / "figures" / "Figure1.png",
        package_root / "tables" / "Table1.csv",
        delivered_root / "manuscript" / "current_package.zip",
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("placeholder\n", encoding="utf-8")
    (package_root / "SUBMISSION_TODO.md").write_text(
        "# Submission TODO\n\nPending items:\n- Authors: pending\n- Ethics: pending\n",
        encoding="utf-8",
    )
    (package_root / "submission_manifest.json").write_text(
        json.dumps(
            {
                "figures": [{"figure_id": "F1"}],
                "tables": [{"table_id": "T1"}],
                "surface_qc": {"status": "pass", "failures": []},
            }
        ),
        encoding="utf-8",
    )
    unknown_root = workspace_root / "studies" / "unknown"
    unknown_root.mkdir(parents=True)
    (unknown_root / "study.yaml").write_text("study_id: unknown\n", encoding="utf-8")

    def fake_status(*, study_id, **_):
        study_root = delivered_root if study_id == "package-ready" else unknown_root
        return {
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_status": "paused",
            "active_run_id": None,
        }

    monkeypatch.setattr(cli.study_runtime_router, "study_runtime_status", fake_status)

    exit_code = cli.main(["study-state-matrix", "--profile", str(profile_path), "--format", "json"])
    captured = capsys.readouterr()
    rows = {row["study_id"]: row for row in json.loads(captured.out)["domain_transition_table"]["rows"]}

    assert exit_code == 0
    assert rows["package-ready"]["decision_type"] == "delivered_package_handoff"
    assert rows["package-ready"]["typed_blocker"]["blocker_id"] == "package_delivered_not_publication_authority"
    assert rows["package-ready"]["guard_boundary"]["opl_generic_runner_may_resume"] is False
    assert rows["unknown"]["decision_type"] == "fail_closed"
    assert rows["unknown"]["typed_blocker"]["blocker_id"] == "domain_transition_unclassified"
