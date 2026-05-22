from __future__ import annotations

import hashlib

from .shared import *  # noqa: F403,F401

def test_sidecar_dispatch_accepts_runtime_recovery_without_writing_truth(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    write_profile(profile_path, workspace_root=workspace_root)
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "frt_001",
            "domain_id": "medautoscience",
            "task_kind": "domain_route/recover",
            "payload": {"profile": str(profile_path), "study_id": "001-risk"},
            "attempts": 1,
            "source": "opl_family_runtime",
            "authority_boundary": {
                "provider": "online_runtime_transport_only",
                "opl": "typed_queue_and_dispatch_only",
                "domain": "truth_quality_artifact_gate_owner",
            },
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    payload = json.loads(captured.out)
    assert payload["surface_kind"] == "mas_family_sidecar_dispatch_receipt"
    assert payload["accepted"] is True
    assert payload["will_start_llm_worker"] is False
    assert payload["dispatch"]["action_type"] == "domain_route_recover"
    assert payload["dispatch"]["recommended_domain_command"].startswith("uv run python -m med_autoscience.cli owner-route-reconcile")
    assert payload["authority_boundary"]["writes_domain_truth"] is False
    assert payload["authority_boundary"]["writes_artifact_gate"] is False
    assert payload["forbidden_write_guard_proof"]["result"] == "accepted_no_forbidden_writes"
    assert payload["forbidden_write_guard_proof"]["can_write_domain_truth"] is False
    assert Path(workspace_root / payload["receipt_ref"]).is_file()
    assert not (workspace_root / ".ds" / "user_message_queue.json").exists()
    assert not (workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "manuscript" / "current_package").exists()
    assert not (study_root / "current_package.zip").exists()


def test_sidecar_dispatch_executes_reconcile_apply_inside_mas_owner(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    adapter = importlib.import_module("med_autoscience.controllers.owner_route_handoff_parts.dispatch_orchestration")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    calls: list[dict[str, object]] = []

    def fake_reconcile_domain_routes(*, profile, study_ids, mode: str, apply: bool) -> dict[str, object]:
        calls.append({"profile": profile.name, "study_ids": tuple(study_ids), "mode": mode, "apply": apply})
        return {
            "surface": "domain_route_reconcile_receipt",
            "resolved_studies": list(study_ids),
            "will_start_llm": True,
            "codex_dispatch_count": 1,
            "blocked_count": 0,
        }

    monkeypatch.setattr(adapter.domain_route_reconcile, "reconcile_domain_routes", fake_reconcile_domain_routes)
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "frt_reconcile",
            "domain_id": "medautoscience",
            "task_kind": "domain_route/reconcile-apply",
            "payload": {"profile": str(profile_path), "study_id": "001-risk"},
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert calls == [{"profile": "nfpitnet", "study_ids": ("001-risk",), "mode": "developer_apply_safe", "apply": True}]
    assert payload["accepted"] is True
    assert payload["will_start_llm_worker"] is True
    assert payload["dispatch"]["execution_policy"] == "mas_owner_reconcile_apply"
    assert payload["dispatch"]["result"]["surface"] == "domain_route_reconcile_receipt"
    assert payload["authority_boundary"]["writes_domain_truth"] is False


def test_sidecar_dispatch_executes_paper_repair_work_unit_inside_mas_owner(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    write_profile(profile_path, workspace_root=workspace_root)
    manuscript = study_root / "paper" / "manuscript.md"
    manuscript.parent.mkdir(parents=True, exist_ok=True)
    manuscript.write_text("The original claim is supported.\n", encoding="utf-8")
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "paper-task-001",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/repair-recheck",
            "payload": {
                "profile": str(profile_path),
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "repair_work_unit": {
                    "unit_id": "unit-1",
                    "work_unit_type": "text_repair",
                    "owner": "quality_repair_batch",
                    "callable_surface": "paper_repair_executor.dispatch_repair_work_unit",
                    "source_fingerprint": "sha256:unit-1",
                    "source_refs": ["artifacts/publication_eval/latest.json"],
                    "gate_replay_target": "publication_eval/latest.json",
                    "canonical_patch": {
                        "target_text": "The original claim is supported.",
                        "replacement_text": "The association is directionally consistent but requires restrained interpretation.",
                    },
                },
            },
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["accepted"] is True
    assert payload["dispatch"]["action_type"] == "paper_repair_executor_dispatch"
    assert payload["will_start_llm_worker"] is False
    paper_receipt = payload["dispatch"]["result"]
    assert paper_receipt["execution_status"] == "executed"
    assert paper_receipt["repair_execution_evidence"]["progress_delta_candidate"] is True
    assert paper_receipt["owner_receipt"]["direct_current_package_write"] is False
    assert (study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json").is_file()
    assert (study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json").is_file()
    assert not (study_root / "manuscript" / "current_package").exists()


def test_sidecar_dispatch_routes_quality_repair_batch_callable_inside_mas_owner(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    adapter = importlib.import_module("med_autoscience.controllers.owner_route_handoff_parts.dispatch_orchestration")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    write_profile(profile_path, workspace_root=workspace_root)
    evidence_path = study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
    calls: list[dict[str, object]] = []

    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        calls.append(kwargs)
        evidence = {
            "surface": "repair_execution_evidence",
            "progress_delta_candidate": True,
            "canonical_artifact_delta": {"meaningful_artifact_delta": True},
        }
        _write_json(evidence_path, evidence)
        return {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
            "repair_execution_evidence": evidence,
            "repair_execution_evidence_path": str(evidence_path),
        }

    monkeypatch.setattr(adapter.paper_repair_executor.quality_repair_batch, "run_quality_repair_batch", fake_run_quality_repair_batch)
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "paper-task-quality-batch",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/repair-recheck",
            "payload": {
                "profile": str(profile_path),
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "repair_work_unit": {
                    "unit_id": "unit-quality-batch",
                    "work_unit_type": "text_repair",
                    "owner": "quality_repair_batch",
                    "callable_surface": "quality_repair_batch.run_quality_repair_batch",
                    "source_fingerprint": "sha256:unit-quality-batch",
                    "source_refs": ["artifacts/publication_eval/latest.json"],
                    "gate_replay_target": "publication_eval/latest.json",
                },
            },
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["accepted"] is True
    assert payload["dispatch"]["action_type"] == "paper_repair_executor_dispatch"
    paper_receipt = payload["dispatch"]["result"]
    assert paper_receipt["execution_status"] == "executed"
    assert paper_receipt["owner_callable_surface"] == "quality_repair_batch.run_quality_repair_batch"
    assert paper_receipt["owner_receipt"]["direct_current_package_write"] is False
    assert calls[0]["profile"].name == "nfpitnet"
    assert calls[0]["study_id"] == "001-risk"
    assert calls[0]["study_root"] == study_root.resolve()
    assert calls[0]["quest_id"] == "quest-001"
    assert (study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json").is_file()
    assert not (study_root / "manuscript" / "current_package").exists()


def test_sidecar_dispatch_accepts_quality_repair_writer_handoff_without_dead_lettering(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    adapter = importlib.import_module("med_autoscience.controllers.owner_route_handoff_parts.dispatch_orchestration")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)
    evidence_path = study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"

    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        evidence = {
            "surface": "repair_execution_evidence",
            "status": "blocked",
            "progress_delta_candidate": False,
            "blockers": ["manuscript_story_surface_delta_missing"],
            "canonical_artifact_delta": {
                "status": "blocked",
                "meaningful_artifact_delta": False,
            },
            "manuscript_surface_hygiene": {
                "status": "blocked",
                "blockers": ["manuscript_story_surface_delta_missing"],
                "story_surface_delta_required": True,
                "story_surface_delta_present": False,
            },
        }
        _write_json(evidence_path, evidence)
        return {
            "ok": True,
            "status": "handoff_ready",
            "blocked_reason": None,
            "next_owner": "write",
            "record_path": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
            "repair_execution_evidence": evidence,
            "repair_execution_evidence_path": str(evidence_path),
            "writer_worker_handoff": {
                "surface": "default_executor_dispatch_request",
                "dispatch_status": "ready",
                "next_executable_owner": "write",
                "required_output_surface": (
                    "canonical manuscript story-surface delta or "
                    "typed blocker:manuscript_story_surface_delta_missing"
                ),
            },
        }

    monkeypatch.setattr(adapter.paper_repair_executor.quality_repair_batch, "run_quality_repair_batch", fake_run_quality_repair_batch)
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "paper-task-quality-batch-blocked",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/repair-recheck",
            "payload": {
                "profile": str(profile_path),
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "repair_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "work_unit_type": "text_repair",
                    "owner": "quality_repair_batch",
                    "callable_surface": "quality_repair_batch.run_quality_repair_batch",
                    "source_fingerprint": "sha256:medical-prose-write-repair",
                    "source_refs": ["artifacts/publication_eval/latest.json"],
                    "gate_replay_target": "publication_eval/latest.json",
                },
            },
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["accepted"] is True
    assert payload["will_start_llm_worker"] is True
    assert "reason" not in payload
    paper_receipt = payload["dispatch"]["result"]
    assert paper_receipt["accepted"] is True
    assert paper_receipt["execution_status"] == "handoff_ready"
    assert paper_receipt["typed_blocker"] is None
    assert paper_receipt["canonical_artifact_delta"]["meaningful_artifact_delta"] is False
    handoff = paper_receipt["writer_worker_handoff"]
    assert handoff["surface"] == "default_executor_dispatch_request"
    assert handoff["dispatch_status"] == "ready"
    assert handoff["next_executable_owner"] == "write"
    assert "canonical manuscript story-surface delta" in handoff["required_output_surface"]
    assert payload["dispatch"]["downstream_worker_handoff"]["next_executable_owner"] == "write"


def test_sidecar_dispatch_prefers_runtime_binding_quest_id_for_quality_repair_batch_callable(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    adapter = importlib.import_module("med_autoscience.controllers.owner_route_handoff_parts.dispatch_orchestration")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"
    write_profile(profile_path, workspace_root=workspace_root)
    (study_root / "runtime_binding.yaml").parent.mkdir(parents=True, exist_ok=True)
    (study_root / "runtime_binding.yaml").write_text(
        "schema_version: 1\n"
        "study_id: 003-dpcc-primary-care-phenotype-treatment-gap\n"
        "quest_id: 003-dpcc-primary-care-phenotype-treatment-gap\n",
        encoding="utf-8",
    )
    calls: list[dict[str, object]] = []

    def fake_run_quality_repair_batch(**kwargs) -> dict[str, object]:
        calls.append(kwargs)
        evidence_path = study_root / "artifacts" / "controller" / "repair_execution_evidence" / "latest.json"
        evidence = {
            "surface": "repair_execution_evidence",
            "progress_delta_candidate": True,
            "canonical_artifact_delta": {"meaningful_artifact_delta": True},
        }
        _write_json(evidence_path, evidence)
        return {
            "ok": True,
            "status": "executed",
            "record_path": str(study_root / "artifacts" / "controller" / "quality_repair_batch" / "latest.json"),
            "repair_execution_evidence": evidence,
            "repair_execution_evidence_path": str(evidence_path),
        }

    monkeypatch.setattr(adapter.paper_repair_executor.quality_repair_batch, "run_quality_repair_batch", fake_run_quality_repair_batch)
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "paper-task-quality-batch-canonical-quest",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/repair-recheck",
            "payload": {
                "profile": str(profile_path),
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "repair_work_unit": {
                    "unit_id": "quality_repair_batch",
                    "work_unit_type": "text_repair",
                    "owner": "quality_repair_batch",
                    "callable_surface": "quality_repair_batch.run_quality_repair_batch",
                    "source_fingerprint": "sha256:quality-repair-batch",
                    "source_refs": ["artifacts/publication_eval/latest.json"],
                    "gate_replay_target": "publication_eval/latest.json",
                },
            },
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["accepted"] is True
    assert calls[0]["quest_id"] == "003-dpcc-primary-care-phenotype-treatment-gap"


def test_sidecar_dispatch_routes_embedded_ai_reviewer_callable_inside_mas_owner(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    adapter = importlib.import_module("med_autoscience.controllers.owner_route_handoff_parts.dispatch_orchestration")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    write_profile(profile_path, workspace_root=workspace_root)
    calls: list[dict[str, object]] = []

    def fake_dispatch_domain_owner_actions(**kwargs) -> dict[str, object]:
        calls.append(kwargs)
        return {
            "surface": "default_executor_dispatch_executor",
            "executed_count": 1,
            "blocked_count": 0,
        }

    monkeypatch.setattr(
        adapter.paper_repair_executor.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        fake_dispatch_domain_owner_actions,
    )
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "paper-task-ai-reviewer-callable",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/repair-recheck",
            "payload": {
                "profile": str(profile_path),
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "repair_work_unit": {
                    "unit_id": "unit-ai-reviewer",
                    "work_unit_type": "ai_reviewer_recheck",
                    "owner": "ai_reviewer",
                    "callable_surface": (
                        "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
                    ),
                    "source_fingerprint": "sha256:unit-ai-reviewer",
                    "source_refs": ["artifacts/publication_eval/latest.json"],
                    "gate_replay_target": "controller_decisions/latest.json",
                },
            },
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["accepted"] is True
    assert payload["dispatch"]["action_type"] == "paper_repair_executor_dispatch"
    paper_receipt = payload["dispatch"]["result"]
    assert paper_receipt["execution_status"] == "executed"
    assert paper_receipt["owner_callable_surface"] == (
        "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
    )
    assert len(calls) == 1
    assert calls[0]["profile"].name == "nfpitnet"
    assert calls[0]["study_ids"] == ("001-risk",)
    assert calls[0]["action_types"] == ("return_to_ai_reviewer_workflow",)
    assert calls[0]["mode"] == "developer_apply_safe"
    assert calls[0]["apply"] is True
    assert (study_root / "artifacts" / "controller" / "repair_execution_receipts" / "latest.json").is_file()
    assert not (study_root / "manuscript" / "current_package").exists()


def test_sidecar_dispatch_preserves_embedded_ai_reviewer_callable_blocker(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    adapter = importlib.import_module("med_autoscience.controllers.owner_route_handoff_parts.dispatch_orchestration")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)

    def fake_dispatch_domain_owner_actions(**_kwargs) -> dict[str, object]:
        return {
            "surface": "default_executor_dispatch_executor",
            "executed_count": 0,
            "blocked_count": 1,
            "repeat_suppressed_count": 0,
            "executions": [
                {
                    "execution_status": "blocked",
                    "blocked_reason": "ai_reviewer_request_missing",
                    "owner_callable_surface": (
                        "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
                    ),
                }
            ],
        }

    monkeypatch.setattr(
        adapter.paper_repair_executor.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        fake_dispatch_domain_owner_actions,
    )
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "paper-task-ai-reviewer-callable-blocked",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/repair-recheck",
            "payload": {
                "profile": str(profile_path),
                "study_id": "001-risk",
                "quest_id": "quest-001",
                "repair_work_unit": {
                    "unit_id": "unit-ai-reviewer-blocked",
                    "work_unit_type": "ai_reviewer_recheck",
                    "owner": "ai_reviewer",
                    "callable_surface": (
                        "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
                    ),
                    "source_fingerprint": "sha256:unit-ai-reviewer-blocked",
                    "source_refs": ["artifacts/publication_eval/latest.json"],
                    "gate_replay_target": "controller_decisions/latest.json",
                },
            },
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    paper_receipt = payload["dispatch"]["result"]
    assert paper_receipt["accepted"] is False
    assert paper_receipt["execution_status"] == "blocked"
    assert paper_receipt["typed_blocker"] == "ai_reviewer_request_missing"


def test_sidecar_dispatch_replays_paper_repair_when_owner_capability_changes(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    adapter = importlib.import_module("med_autoscience.controllers.owner_route_handoff_parts.dispatch_orchestration")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    calls: list[dict[str, object]] = []

    def fake_dispatch_domain_owner_actions(**kwargs) -> dict[str, object]:
        calls.append(kwargs)
        return {
            "surface": "default_executor_dispatch_executor",
            "executed_count": 1,
            "blocked_count": 0,
        }

    monkeypatch.setattr(
        adapter.paper_repair_executor.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        fake_dispatch_domain_owner_actions,
    )
    task_path = tmp_path / "task.json"
    task = {
        "task_id": "paper-task-ai-reviewer-callable",
        "domain_id": "medautoscience",
        "task_kind": "paper_autonomy/repair-recheck",
        "source_fingerprint": "reviewer-fp",
        "payload": {
            "profile": str(profile_path),
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "repair_work_unit": {
                "unit_id": "unit-ai-reviewer",
                "work_unit_type": "ai_reviewer_recheck",
                "owner": "ai_reviewer",
                "callable_surface": (
                    "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
                ),
                "source_fingerprint": "sha256:unit-ai-reviewer",
                "source_refs": ["artifacts/publication_eval/latest.json"],
                "gate_replay_target": "controller_decisions/latest.json",
            },
        },
    }
    _write_json(task_path, task)

    stale_receipt_dir = workspace_root / "artifacts" / "runtime" / "opl_family_sidecar" / "dispatch_receipts"
    stale_receipt_dir.mkdir(parents=True, exist_ok=True)
    stale_key = "paper-task-ai-reviewer-callable:reviewer-fp"
    stale_receipt_path = stale_receipt_dir / f"{hashlib.sha256(stale_key.encode('utf-8')).hexdigest()[:20]}.json"
    _write_json(
        stale_receipt_path,
        {
            "surface_kind": "mas_family_sidecar_dispatch_receipt",
            "version": "mas-family-sidecar.v1",
            "accepted": False,
            "task_id": "paper-task-ai-reviewer-callable",
            "task_kind": "paper_autonomy/repair-recheck",
            "source_fingerprint": "reviewer-fp",
            "dispatch": {
                "action_type": "paper_repair_executor_dispatch",
                "result": {
                    "surface": "paper_repair_executor",
                    "accepted": False,
                    "execution_status": "blocked",
                    "typed_blocker": "owner_callable_surface_missing",
                    "source_fingerprint": "stale-domain-result",
                },
            },
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload.get("idempotent_noop") is None
    assert payload["accepted"] is True
    assert payload["dispatch"]["result"]["execution_status"] == "executed"
    assert payload["dispatch"]["result"]["owner_callable_surface"] == (
        "ai_reviewer_publication_eval_workflow.run_ai_reviewer_publication_eval_workflow"
    )
    assert len(calls) == 1
    assert calls[0]["action_types"] == ("return_to_ai_reviewer_workflow",)
    assert payload["receipt_ref"].startswith("artifacts/runtime/opl_family_sidecar/dispatch_receipts/")
    assert payload["receipt_ref"] != str(stale_receipt_path.relative_to(workspace_root))


def test_sidecar_dispatch_routes_paper_ai_reviewer_recheck_to_supervisor_executor(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    adapter = importlib.import_module("med_autoscience.controllers.owner_route_handoff_parts.dispatch_orchestration")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    calls: list[dict[str, object]] = []

    def fake_dispatch_domain_owner_actions(
        *,
        profile,
        study_ids,
        action_types,
        mode: str,
        apply: bool,
        managed_runtime_worker: bool = False,
    ) -> dict[str, object]:
        calls.append(
            {
                "profile": profile.name,
                "study_ids": tuple(study_ids),
                "action_types": tuple(action_types),
                "mode": mode,
                "apply": apply,
            }
        )
        return {
            "surface": "domain_owner_action_dispatch_execution",
            "executed_count": 1,
            "blocked_count": 0,
        }

    monkeypatch.setattr(
        adapter.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        fake_dispatch_domain_owner_actions,
    )
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "paper-ai-reviewer-001",
            "domain_id": "medautoscience",
            "task_kind": "paper_autonomy/ai-reviewer-recheck",
            "payload": {"profile": str(profile_path), "study_id": "001-risk"},
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["dispatch"]["action_type"] == "ai_reviewer_recheck_execute_dispatch"
    assert payload["dispatch"]["result"]["executed_count"] == 1
    assert calls == [
        {
            "profile": "nfpitnet",
            "study_ids": ("001-risk",),
            "action_types": ("return_to_ai_reviewer_workflow",),
            "mode": "developer_apply_safe",
            "apply": True,
        }
    ]


def test_sidecar_dispatch_publication_aftercare_tasks_use_runtime_owner_chain(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    adapter = importlib.import_module("med_autoscience.controllers.owner_route_handoff_parts.dispatch_orchestration")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    write_profile(profile_path, workspace_root=workspace_root)
    reconcile_calls: list[dict[str, object]] = []
    reviewer_calls: list[dict[str, object]] = []

    def fake_reconcile_domain_routes(*, profile, study_ids, mode: str, apply: bool) -> dict[str, object]:
        reconcile_calls.append({"profile": profile.name, "study_ids": tuple(study_ids), "mode": mode, "apply": apply})
        return {"surface": "domain_route_reconcile_receipt", "will_start_llm": True}

    def fake_dispatch_domain_owner_actions(
        *,
        profile,
        study_ids,
        action_types,
        mode: str,
        apply: bool,
        managed_runtime_worker: bool = False,
    ) -> dict[str, object]:
        reviewer_calls.append(
            {
                "profile": profile.name,
                "study_ids": tuple(study_ids),
                "action_types": tuple(action_types),
                "mode": mode,
                "apply": apply,
            }
        )
        return {"surface": "domain_owner_action_dispatch_execution", "executed_count": 1}

    monkeypatch.setattr(adapter.domain_route_reconcile, "reconcile_domain_routes", fake_reconcile_domain_routes)
    monkeypatch.setattr(
        adapter.domain_owner_action_dispatch,
        "dispatch_domain_owner_actions",
        fake_dispatch_domain_owner_actions,
    )
    analysis_task_path = tmp_path / "analysis-task.json"
    reviewer_task_path = tmp_path / "reviewer-task.json"
    _write_json(
        analysis_task_path,
        {
            "task_id": "aftercare-analysis",
            "domain_id": "medautoscience",
            "task_kind": "publication_aftercare/analysis-queue-progress",
            "source_fingerprint": "analysis-fp",
            "payload": {"profile": str(profile_path), "study_id": "DM002"},
        },
    )
    _write_json(
        reviewer_task_path,
        {
            "task_id": "aftercare-reviewer",
            "domain_id": "medautoscience",
            "task_kind": "publication_aftercare/reviewer-refresh",
            "source_fingerprint": "reviewer-fp",
            "payload": {"profile": str(profile_path), "study_id": "DM002"},
        },
    )

    analysis_exit = cli.main(["sidecar", "dispatch", "--task", str(analysis_task_path), "--format", "json"])
    analysis_payload = json.loads(capsys.readouterr().out)
    reviewer_exit = cli.main(["sidecar", "dispatch", "--task", str(reviewer_task_path), "--format", "json"])
    reviewer_payload = json.loads(capsys.readouterr().out)

    assert analysis_exit == 0
    assert reviewer_exit == 0
    assert analysis_payload["dispatch"]["action_type"] == "domain_route_reconcile_apply"
    assert analysis_payload["dispatch"]["execution_policy"] == "mas_owner_reconcile_apply"
    assert reviewer_payload["dispatch"]["action_type"] == "ai_reviewer_recheck_execute_dispatch"
    assert reviewer_payload["dispatch"]["execution_policy"] == "mas_owner_ai_reviewer_execute_dispatch"
    assert reconcile_calls == [{"profile": "nfpitnet", "study_ids": ("DM002",), "mode": "developer_apply_safe", "apply": True}]
    assert reviewer_calls == [
        {
            "profile": "nfpitnet",
            "study_ids": ("DM002",),
            "action_types": ("return_to_ai_reviewer_workflow",),
            "mode": "developer_apply_safe",
            "apply": True,
        }
    ]
    assert analysis_payload["authority_boundary"]["writes_domain_truth"] is False
    assert reviewer_payload["authority_boundary"]["writes_artifact_gate"] is False
    assert analysis_payload["forbidden_write_guard_proof"]["can_authorize_publication_quality"] is False


def test_sidecar_export_does_not_auto_ticket_stop_loss_or_human_gate(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    workspace_root = tmp_path / "workspace"
    profile_path = tmp_path / "profile.local.toml"
    stop_loss_root = workspace_root / "studies" / "stop-loss-study"
    human_gate_root = workspace_root / "studies" / "human-gate-study"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(
        stop_loss_root / "artifacts" / "controller_decisions" / "latest.json",
        {"decision_type": "stop_loss", "route_target": "stop"},
    )
    _write_json(
        stop_loss_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {"state": "breach", "breach_reason": "same_fingerprint_loop"},
    )
    _write_json(
        human_gate_root / "artifacts" / "controller_decisions" / "latest.json",
        {"requires_human_confirmation": True, "family_human_gates": [{"gate_id": "confirm-target"}]},
    )
    _write_json(
        human_gate_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {"state": "breach", "breach_reason": "same_fingerprint_loop"},
    )

    exit_code = cli.main(["sidecar", "export", "--profile", str(profile_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert payload["pending_family_tasks"] == []
    assert payload["studies"][0]["autonomy_continuation"]["eligible_for_auto_dispatch"] is False
    assert payload["studies"][1]["autonomy_continuation"]["eligible_for_auto_dispatch"] is False


def test_sidecar_dispatch_rejects_domain_truth_writes(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "frt_forbidden",
            "domain_id": "medautoscience",
            "task_kind": "artifact/override",
            "payload": {"domain_truth_write": True, "profile": "/tmp/profile.toml"},
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    captured = capsys.readouterr()

    assert exit_code == 1
    payload = json.loads(captured.out)
    assert payload["surface_kind"] == "mas_family_sidecar_dispatch_receipt"
    assert payload["accepted"] is False
    assert payload["forbidden_domain_truth_write"] is True
    assert payload["reason"] == "domain_truth_or_artifact_gate_write_forbidden"
    assert payload["forbidden_requested_writes"] == ["domain_truth_write"]
    guard = payload["forbidden_write_guard_proof"]
    assert guard["surface_kind"] == "mas_opl_forbidden_write_guard_proof"
    assert guard["result"] == "blocked"
    assert guard["guard_mode"] == "fail_closed"
    assert guard["can_write_domain_truth"] is False


def test_sidecar_dispatch_rejects_opl_attempt_truth_substitution(tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "attempt-substitution",
            "domain_id": "medautoscience",
            "task_kind": "domain_route/recover",
            "payload": {
                "profile": "/tmp/profile.toml",
                "study_id": "001-risk",
                "requested_writes": ["controller_decisions", "publication_eval"],
                "opl_attempt_status": "completed",
            },
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["accepted"] is False
    assert payload["reason"] == "domain_truth_or_artifact_gate_write_forbidden"
    assert payload["forbidden_requested_writes"] == ["controller_decisions", "publication_eval"]
    guard = payload["forbidden_write_guard_proof"]
    assert guard["forbidden_requested_writes"] == ["controller_decisions", "publication_eval"]
    assert guard["can_authorize_publication_quality"] is False


def test_sidecar_dispatch_rejects_opl_memory_body_or_router_acceptance_write(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "memory-body-write",
            "domain_id": "medautoscience",
            "task_kind": "study_progress/read",
            "payload": {
                "profile": "/tmp/profile.toml",
                "study_id": "001-risk",
                "requested_writes": [
                    "publication_route_memory_body",
                    "memory_write_router_accept",
                ],
            },
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["accepted"] is False
    assert payload["reason"] == "domain_truth_or_artifact_gate_write_forbidden"
    assert payload["forbidden_requested_writes"] == [
        "publication_route_memory_body",
        "memory_write_router_accept",
    ]
    guard = payload["forbidden_write_guard_proof"]
    assert guard["guard_owner"] == "med-autoscience"
    assert guard["can_write_domain_truth"] is False


def test_sidecar_dispatch_rejects_opl_substrate_authority_surface_writes(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    task_path = tmp_path / "task.json"
    _write_json(
        task_path,
        {
            "task_id": "substrate-authority-write",
            "domain_id": "medautoscience",
            "task_kind": "study_progress/read",
            "payload": {
                "profile": "/tmp/profile.toml",
                "study_id": "001-risk",
                "requested_writes": [
                    "publication_eval",
                    "controller_decisions",
                    "manuscript/current_package",
                    "current_package.zip",
                    "evidence_ledger",
                    "review_ledger",
                    "publication_authority",
                    "artifact_authority",
                ],
            },
        },
    )

    exit_code = cli.main(["sidecar", "dispatch", "--task", str(task_path), "--format", "json"])
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 1
    assert payload["accepted"] is False
    assert payload["reason"] == "domain_truth_or_artifact_gate_write_forbidden"
    assert payload["forbidden_requested_writes"] == [
        "publication_eval",
        "controller_decisions",
        "manuscript/current_package",
        "current_package.zip",
        "evidence_ledger",
        "review_ledger",
        "publication_authority",
        "artifact_authority",
    ]
    guard = payload["forbidden_write_guard_proof"]
    assert guard["can_write_domain_truth"] is False
    assert guard["can_write_current_package"] is False
    assert guard["can_override_artifact_gate"] is False
