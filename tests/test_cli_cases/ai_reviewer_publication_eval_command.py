from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_publication_ai_reviewer_eval_command_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    payload_file = tmp_path / "publication_eval.json"
    payload_file.write_text(
        json.dumps(
            {
                "eval_id": "publication-eval::001-risk::quest-001::2026-04-26T22:00:00+00:00",
                "assessment_provenance": {"owner": "ai_reviewer"},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    called: dict[str, object] = {}

    def fake_materialize(
        *,
        profile,
        study_id: str | None,
        study_root: Path | None,
        entry_mode: str | None,
        record: dict,
        source: str,
    ) -> dict:
        called["profile"] = profile
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["entry_mode"] = entry_mode
        called["record"] = record
        called["source"] = source
        return {
            "status": "materialized",
            "eval_id": record["eval_id"],
            "assessment_owner": record["assessment_provenance"]["owner"],
        }

    monkeypatch.setattr(
        cli.ai_reviewer_publication_eval,
        "materialize_ai_reviewer_publication_eval",
        fake_materialize,
    )

    exit_code = cli.main(
        [
            "publication",
            "materialize-ai-reviewer-eval",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
            "--payload-file",
            str(payload_file),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_id"] == "001-risk"
    assert called["study_root"] is None
    assert called["entry_mode"] is None
    assert called["record"]["assessment_provenance"]["owner"] == "ai_reviewer"
    assert called["source"] == "cli"
    assert json.loads(captured.out)["assessment_owner"] == "ai_reviewer"


def test_publication_ai_reviewer_record_command_dispatches_record_materializer(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    payload_file = tmp_path / "publication_eval_record.json"
    payload_file.write_text(
        json.dumps(
            {
                "eval_id": "publication-eval::001-risk::quest-001::2026-04-26T22:00:00+00:00",
                "assessment_provenance": {"owner": "ai_reviewer"},
                "evaluation_scope": "publication",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    called: dict[str, object] = {}

    def fake_materialize_record(
        *,
        profile,
        study_id: str | None,
        study_root: Path | None,
        entry_mode: str | None,
        record: dict,
        source: str,
        build_production_trace: bool = False,
    ) -> dict:
        called["profile"] = profile
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["entry_mode"] = entry_mode
        called["record"] = record
        called["source"] = source
        called["build_production_trace"] = build_production_trace
        return {
            "status": "materialized",
            "eval_id": record["eval_id"],
            "assessment_owner": record["assessment_provenance"]["owner"],
            "publication_eval_surface": "not_written",
        }

    monkeypatch.setattr(
        cli.ai_reviewer_publication_eval,
        "materialize_ai_reviewer_publication_eval_record",
        fake_materialize_record,
    )

    exit_code = cli.main(
        [
            "publication",
            "materialize-ai-reviewer-record",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
            "--payload-file",
            str(payload_file),
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_id"] == "001-risk"
    assert called["study_root"] is None
    assert called["entry_mode"] is None
    assert called["record"]["evaluation_scope"] == "publication"
    assert called["source"] == "cli"
    assert called["build_production_trace"] is False
    assert json.loads(captured.out)["publication_eval_surface"] == "not_written"


def test_publication_ai_reviewer_record_command_can_request_production_trace_rebuild(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    payload_file = tmp_path / "publication_eval_record.json"
    payload_file.write_text(
        json.dumps(
            {
                "eval_id": "publication-eval::001-risk::quest-001::2026-04-26T22:00:00+00:00",
                "assessment_provenance": {"owner": "ai_reviewer"},
                "evaluation_scope": "publication",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    called: dict[str, object] = {}

    def fake_materialize_record(
        *,
        profile,
        study_id: str | None,
        study_root: Path | None,
        entry_mode: str | None,
        record: dict,
        source: str,
        build_production_trace: bool,
    ) -> dict:
        called["build_production_trace"] = build_production_trace
        return {
            "status": "materialized",
            "eval_id": record["eval_id"],
            "assessment_owner": record["assessment_provenance"]["owner"],
            "publication_eval_surface": "not_written",
        }

    monkeypatch.setattr(
        cli.ai_reviewer_publication_eval,
        "materialize_ai_reviewer_publication_eval_record",
        fake_materialize_record,
    )

    exit_code = cli.main(
        [
            "publication",
            "materialize-ai-reviewer-record",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
            "--payload-file",
            str(payload_file),
            "--build-production-trace",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["build_production_trace"] is True
    assert json.loads(captured.out)["publication_eval_surface"] == "not_written"


def test_publication_ai_reviewer_record_command_runs_identity_guard_before_write(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    payload_file = tmp_path / "publication_eval_record.json"
    payload_file.write_text(
        json.dumps(
            {
                "eval_id": "publication-eval::001-risk::quest-001::2026-04-26T22:00:00+00:00",
                "assessment_provenance": {"owner": "ai_reviewer"},
                "evaluation_scope": "publication",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    called: dict[str, object] = {}

    def fake_plan(
        *,
        profile,
        study_id: str | None,
        study_root: Path | None,
        entry_mode: str | None,
        source: str,
        record: dict | None = None,
        expected_owner: str | None = None,
        expected_action_type: str | None = None,
        expected_work_unit_id: str | None = None,
        expected_work_unit_fingerprint: str | None = None,
    ) -> dict:
        called["precheck"] = True
        called["precheck_record"] = record
        called["expected_owner"] = expected_owner
        called["expected_action_type"] = expected_action_type
        called["expected_work_unit_id"] = expected_work_unit_id
        called["expected_work_unit_fingerprint"] = expected_work_unit_fingerprint
        return {
            "status": "dry_run",
            "identity_guard": {"matched": True},
            "payload_guard": {"matched": True},
            "written_files": [],
        }

    def fake_materialize_record(
        *,
        profile,
        study_id: str | None,
        study_root: Path | None,
        entry_mode: str | None,
        record: dict,
        source: str,
        build_production_trace: bool = False,
    ) -> dict:
        called["materialized"] = True
        return {
            "status": "materialized",
            "eval_id": record["eval_id"],
            "assessment_owner": record["assessment_provenance"]["owner"],
            "publication_eval_surface": "not_written",
        }

    monkeypatch.setattr(
        cli.ai_reviewer_publication_eval,
        "plan_ai_reviewer_publication_eval_record_materialization",
        fake_plan,
    )
    monkeypatch.setattr(
        cli.ai_reviewer_publication_eval,
        "materialize_ai_reviewer_publication_eval_record",
        fake_materialize_record,
    )

    exit_code = cli.main(
        [
            "publication",
            "materialize-ai-reviewer-record",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
            "--payload-file",
            str(payload_file),
            "--expected-owner",
            "analysis-campaign",
            "--expected-action-type",
            "run_quality_repair_batch",
            "--expected-work-unit-id",
            "analysis_claim_evidence_repair",
            "--expected-work-unit-fingerprint",
            "publication-blockers::f11710a114497b27",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["precheck"] is True
    assert called["materialized"] is True
    assert called["precheck_record"]["evaluation_scope"] == "publication"
    assert called["expected_owner"] == "analysis-campaign"
    assert called["expected_action_type"] == "run_quality_repair_batch"
    assert called["expected_work_unit_id"] == "analysis_claim_evidence_repair"
    assert called["expected_work_unit_fingerprint"] == "publication-blockers::f11710a114497b27"
    assert json.loads(captured.out)["status"] == "materialized"


def test_publication_ai_reviewer_record_command_stops_when_identity_guard_blocks(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    payload_file = tmp_path / "publication_eval_record.json"
    payload_file.write_text(
        json.dumps(
            {
                "eval_id": "publication-eval::001-risk::quest-001::2026-04-26T22:00:00+00:00",
                "assessment_provenance": {"owner": "ai_reviewer"},
                "evaluation_scope": "publication",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    called: dict[str, object] = {}

    def fake_plan(**kwargs) -> dict:
        called["precheck"] = True
        return {
            "status": "blocked",
            "blocked_reason": "current_owner_identity_mismatch",
            "identity_guard": {"matched": False},
            "payload_guard": {"matched": True},
            "written_files": [],
        }

    def fake_materialize_record(**kwargs) -> dict:
        called["materialized"] = True
        return {"status": "materialized"}

    monkeypatch.setattr(
        cli.ai_reviewer_publication_eval,
        "plan_ai_reviewer_publication_eval_record_materialization",
        fake_plan,
    )
    monkeypatch.setattr(
        cli.ai_reviewer_publication_eval,
        "materialize_ai_reviewer_publication_eval_record",
        fake_materialize_record,
    )

    exit_code = cli.main(
        [
            "publication",
            "materialize-ai-reviewer-record",
            "--profile",
            str(profile_path),
            "--study-id",
            "001-risk",
            "--payload-file",
            str(payload_file),
            "--expected-owner",
            "ai_reviewer",
        ]
    )
    captured = capsys.readouterr()
    output = json.loads(captured.out)

    assert exit_code == 0
    assert called["precheck"] is True
    assert "materialized" not in called
    assert output["status"] == "blocked"
    assert output["blocked_reason"] == "current_owner_identity_mismatch"
    assert output["written_files"] == []


def test_publication_ai_reviewer_record_dry_run_dispatches_no_write_plan(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    write_profile(profile_path)
    called: dict[str, object] = {}

    def fake_plan(
        *,
        profile,
        study_id: str | None,
        study_root: Path | None,
        entry_mode: str | None,
        source: str,
        record: dict | None = None,
        expected_owner: str | None = None,
        expected_action_type: str | None = None,
        expected_work_unit_id: str | None = None,
        expected_work_unit_fingerprint: str | None = None,
    ) -> dict:
        called["profile"] = profile
        called["study_id"] = study_id
        called["study_root"] = study_root
        called["entry_mode"] = entry_mode
        called["source"] = source
        called["record"] = record
        called["expected_owner"] = expected_owner
        called["expected_action_type"] = expected_action_type
        called["expected_work_unit_id"] = expected_work_unit_id
        called["expected_work_unit_fingerprint"] = expected_work_unit_fingerprint
        return {
            "status": "dry_run",
            "dry_run": True,
            "study_id": study_id,
            "owner_callable_surface": "publication materialize-ai-reviewer-record",
            "written_files": [],
        }

    monkeypatch.setattr(
        cli.ai_reviewer_publication_eval,
        "plan_ai_reviewer_publication_eval_record_materialization",
        fake_plan,
    )

    exit_code = cli.main(
        [
            "publication",
            "materialize-ai-reviewer-record",
            "--profile",
            str(profile_path),
            "--study-id",
            "002-dm-china-us-mortality-attribution",
            "--build-production-trace",
            "--dry-run",
            "--expected-owner",
            "ai_reviewer",
            "--expected-action-type",
            "run_quality_repair_batch",
            "--expected-work-unit-id",
            "analysis_claim_evidence_repair",
            "--expected-work-unit-fingerprint",
            "publication-blockers::f11710a114497b27",
        ]
    )
    captured = capsys.readouterr()
    output = json.loads(captured.out)

    assert exit_code == 0
    assert called["profile"].name == "nfpitnet"
    assert called["study_id"] == "002-dm-china-us-mortality-attribution"
    assert called["study_root"] is None
    assert called["entry_mode"] is None
    assert called["source"] == "cli"
    assert called["record"] is None
    assert called["expected_owner"] == "ai_reviewer"
    assert called["expected_action_type"] == "run_quality_repair_batch"
    assert called["expected_work_unit_id"] == "analysis_claim_evidence_repair"
    assert called["expected_work_unit_fingerprint"] == "publication-blockers::f11710a114497b27"
    assert output["status"] == "dry_run"
    assert output["written_files"] == []


def test_ai_reviewer_record_dry_run_plan_reports_current_identity_without_writes(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / study_id
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    evidence_path = study_root / "paper" / "evidence_ledger.json"
    claim_map_path = study_root / "paper" / "claim_evidence_map.json"
    for path in (request_path, evidence_path, claim_map_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text("{}", encoding="utf-8")
    claim_map_path.write_text("{}", encoding="utf-8")
    request_path.write_text(
        json.dumps(
            {
                "surface": "domain_action_request",
                "study_id": study_id,
                "quest_id": study_id,
                "request_kind": "return_to_ai_reviewer_workflow",
                "request_owner": "ai_reviewer",
                "input_contract": {
                    "required_refs": {
                        "evidence_ledger": {"path": str(evidence_path)},
                        "claim_evidence_map": {"path": str(claim_map_path)},
                    }
                },
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                    "stale_record_ref": str(
                        study_root
                        / "artifacts"
                        / "publication_eval"
                        / "ai_reviewer_responses"
                        / "20260620T120049Z_publication_eval_record.json"
                    ),
                    "required_currentness_refs": [str(evidence_path), str(claim_map_path)],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    def fake_read_study_progress(**kwargs) -> dict:
        return {
            "study_id": study_id,
            "quest_id": study_id,
            "study_root": str(study_root),
            "current_work_unit": {
                "status": "typed_blocker",
                "owner": "ai_reviewer",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::f11710a114497b27",
                "phase": "domain_blocked",
                "state": {
                    "typed_blocker": {
                        "reason": "ai_reviewer_record_stale_after_current_inputs",
                        "typed_blocker_ref": "opl://stage_attempts/sat_ae61b9dbbe1e582d76371721",
                    }
                },
            },
        }

    monkeypatch.setattr(module.study_progress_projection, "read_study_progress", fake_read_study_progress)

    result = module.plan_ai_reviewer_publication_eval_record_materialization(
        profile=profile,
        study_id=study_id,
        study_root=None,
        entry_mode=None,
        source="cli",
    )

    assert result["status"] == "dry_run"
    assert result["written_files"] == []
    assert result["study_id"] == study_id
    assert result["owner"] == "ai_reviewer"
    assert result["current_work_unit"]["action_type"] == "run_quality_repair_batch"
    assert result["current_work_unit"]["work_unit_id"] == "analysis_claim_evidence_repair"
    assert result["current_work_unit"]["work_unit_fingerprint"] == "publication-blockers::f11710a114497b27"
    assert result["current_work_unit"]["typed_blocker"]["reason"] == "ai_reviewer_record_stale_after_current_inputs"
    assert result["request"]["blocked_reason"] == "ai_reviewer_record_stale_after_current_inputs"
    assert result["required_currentness_refs"] == [str(evidence_path), str(claim_map_path)]
    assert result["required_input_refs"]["evidence_ledger"] == str(evidence_path)
    assert result["required_input_refs"]["claim_evidence_map"] == str(claim_map_path)
    assert result["expected_write_surfaces"] == [
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
    ]
    assert "artifacts/publication_eval/latest.json" in result["forbidden_surfaces"]
    assert "artifacts/controller_decisions/latest.json" in result["forbidden_surfaces"]
    assert result["publication_eval_surface"] == "not_written"
    assert result["publication_eval_record_surface"] == "not_written"
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses").exists()


def test_ai_reviewer_record_dry_run_rejects_stale_payload_currentness_refs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / study_id
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    current_evidence_path = study_root / "paper" / "evidence_ledger.json"
    current_claim_map_path = study_root / "paper" / "claim_evidence_map.json"
    stale_evidence_path = study_root / "old" / "evidence_ledger.json"
    stale_claim_map_path = study_root / "old" / "claim_evidence_map.json"
    for path in (request_path, current_evidence_path, current_claim_map_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    current_evidence_path.write_text("{}", encoding="utf-8")
    current_claim_map_path.write_text("{}", encoding="utf-8")
    request_path.write_text(
        json.dumps(
            {
                "surface": "domain_action_request",
                "study_id": study_id,
                "quest_id": study_id,
                "request_kind": "return_to_ai_reviewer_workflow",
                "request_owner": "ai_reviewer",
                "input_contract": {
                    "required_refs": {
                        "evidence_ledger": {"path": str(current_evidence_path)},
                        "claim_evidence_map": {"path": str(current_claim_map_path)},
                    }
                },
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                    "stale_record_ref": str(
                        study_root
                        / "artifacts"
                        / "publication_eval"
                        / "ai_reviewer_responses"
                        / "20260620T120049Z_publication_eval_record.json"
                    ),
                    "required_currentness_refs": [str(current_evidence_path), str(current_claim_map_path)],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module.study_progress_projection,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": study_id,
            "quest_id": study_id,
            "study_root": str(study_root),
            "current_work_unit": {
                "status": "typed_blocker",
                "owner": "ai_reviewer",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::f11710a114497b27",
            },
        },
    )

    result = module.plan_ai_reviewer_publication_eval_record_materialization(
        profile=profile,
        study_id=study_id,
        study_root=None,
        entry_mode=None,
        source="cli",
        record={
            "surface": "ai_reviewer_record_payload_authoring_target",
            "required_input_refs": {
                "evidence_ledger": str(stale_evidence_path),
                "claim_evidence_map": str(stale_claim_map_path),
            },
            "record_payload": {
                "eval_id": "publication-eval::002::stale",
                "reviewer_operating_system": {
                    "input_bundle": {
                        "evidence_ledger": str(stale_evidence_path),
                        "claim_evidence_map": str(stale_claim_map_path),
                    }
                },
            },
        },
        expected_owner="ai_reviewer",
        expected_action_type="run_quality_repair_batch",
        expected_work_unit_id="analysis_claim_evidence_repair",
        expected_work_unit_fingerprint="publication-blockers::f11710a114497b27",
    )

    assert result["status"] == "blocked"
    assert result["blocked_reason"] == "payload_currentness_mismatch"
    assert result["identity_guard"]["matched"] is True
    assert result["payload_guard"]["matched"] is False
    assert result["payload_guard"]["reason"] == "payload_currentness_mismatch"
    assert result["payload_guard"]["mismatches"] == [
        {
            "surface": "evidence_ledger",
            "expected": str(current_evidence_path),
            "observed": str(stale_evidence_path),
        },
        {
            "surface": "claim_evidence_map",
            "expected": str(current_claim_map_path),
            "observed": str(stale_claim_map_path),
        },
    ]
    assert result["written_files"] == []
    assert result["expected_write_surfaces"] == [
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
    ]
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses").exists()


def test_ai_reviewer_record_dry_run_accepts_current_payload_currentness_refs(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / study_id
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    evidence_path = study_root / "paper" / "evidence_ledger.json"
    claim_map_path = study_root / "paper" / "claim_evidence_map.json"
    for path in (request_path, evidence_path, claim_map_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text("{}", encoding="utf-8")
    claim_map_path.write_text("{}", encoding="utf-8")
    request_path.write_text(
        json.dumps(
            {
                "surface": "domain_action_request",
                "study_id": study_id,
                "quest_id": study_id,
                "request_kind": "return_to_ai_reviewer_workflow",
                "request_owner": "ai_reviewer",
                "input_contract": {
                    "required_refs": {
                        "evidence_ledger": {"path": str(evidence_path)},
                        "claim_evidence_map": {"path": str(claim_map_path)},
                    }
                },
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                    "required_currentness_refs": [str(evidence_path), str(claim_map_path)],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module.study_progress_projection,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": study_id,
            "quest_id": study_id,
            "study_root": str(study_root),
            "current_work_unit": {
                "status": "typed_blocker",
                "owner": "ai_reviewer",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::f11710a114497b27",
            },
        },
    )

    result = module.plan_ai_reviewer_publication_eval_record_materialization(
        profile=profile,
        study_id=study_id,
        study_root=None,
        entry_mode=None,
        source="cli",
        record={
            "surface": "ai_reviewer_record_payload_authoring_target",
            "required_input_refs": {
                "evidence_ledger": str(evidence_path),
                "claim_evidence_map": str(claim_map_path),
            },
            "record_payload": {
                "eval_id": "publication-eval::002::current",
                "reviewer_operating_system": {
                    "input_bundle": {
                        "evidence_ledger": str(evidence_path),
                        "claim_evidence_map": str(claim_map_path),
                    }
                },
            },
        },
        expected_owner="ai_reviewer",
        expected_action_type="run_quality_repair_batch",
        expected_work_unit_id="analysis_claim_evidence_repair",
        expected_work_unit_fingerprint="publication-blockers::f11710a114497b27",
    )

    assert result["status"] == "dry_run"
    assert result["identity_guard"]["matched"] is True
    assert result["payload_guard"]["matched"] is True
    assert result["payload_guard"]["reason"] is None
    assert result["payload_guard"]["mismatches"] == []
    assert result["written_files"] == []
    assert result["expected_write_surfaces"] == [
        "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
    ]
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses").exists()


def test_ai_reviewer_record_dry_run_accepts_current_authoring_target_metadata(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / study_id
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    prose_review_path = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "current_body"
        / "paper"
        / "medical_prose_review.json"
    )
    current_record_ref = str(
        (
            study_root
            / "artifacts"
            / "publication_eval"
            / "ai_reviewer_responses"
            / "20260621T103510Z_publication_eval_record.json"
        ).resolve()
    )
    for path in (request_path, prose_review_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    prose_review_path.write_text("{}", encoding="utf-8")
    request_path.write_text(
        json.dumps(
            {
                "surface": "domain_action_request",
                "study_id": study_id,
                "quest_id": study_id,
                "request_kind": "return_to_ai_reviewer_workflow",
                "request_owner": "ai_reviewer",
                "input_contract": {
                    "required_refs": {
                        "medical_prose_review": {"path": str(prose_review_path.resolve())},
                    }
                },
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                    "stale_record_ref": current_record_ref,
                    "required_currentness_refs": [str(prose_review_path.resolve())],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        module.study_progress_projection,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": study_id,
            "quest_id": study_id,
            "study_root": str(study_root),
            "current_work_unit": {
                "status": "typed_blocker",
                "owner": "ai_reviewer",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::f11710a114497b27",
            },
        },
    )

    result = module.plan_ai_reviewer_publication_eval_record_materialization(
        profile=profile,
        study_id=study_id,
        study_root=None,
        entry_mode=None,
        source="cli",
        record={
            "surface": "ai_reviewer_record_payload_authoring_target",
            "stale_record_ref": current_record_ref,
            "required_currentness_refs": [str(prose_review_path.resolve())],
            "required_input_refs": {"medical_prose_review": str(prose_review_path.resolve())},
            "record_payload": {
                "eval_id": "publication-eval::002::current",
                "reviewer_operating_system": {
                    "input_bundle": {
                        "medical_prose_review": str(prose_review_path.resolve()),
                    }
                },
            },
        },
        expected_owner="ai_reviewer",
        expected_action_type="run_quality_repair_batch",
        expected_work_unit_id="analysis_claim_evidence_repair",
        expected_work_unit_fingerprint="publication-blockers::f11710a114497b27",
    )

    assert result["status"] == "dry_run"
    assert result["payload_guard"]["matched"] is True
    assert result["payload_guard"]["mismatches"] == []
    assert result["payload_guard"]["missing_observed_fields"] == []
    assert result["written_files"] == []


def test_ai_reviewer_record_dry_run_rejects_stale_authoring_target_stale_record_ref(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / study_id
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    prose_review_path = study_root / "paper" / "medical_prose_review.json"
    current_record_ref = str(
        (
            study_root
            / "artifacts"
            / "publication_eval"
            / "ai_reviewer_responses"
            / "20260621T103510Z_publication_eval_record.json"
        ).resolve()
    )
    stale_record_ref = str(
        (
            study_root
            / "artifacts"
            / "publication_eval"
            / "ai_reviewer_responses"
            / "20260609T011045Z_publication_eval_record.json"
        ).resolve()
    )
    for path in (request_path, prose_review_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    prose_review_path.write_text("{}", encoding="utf-8")
    request_path.write_text(
        json.dumps(
            {
                "surface": "domain_action_request",
                "study_id": study_id,
                "quest_id": study_id,
                "request_kind": "return_to_ai_reviewer_workflow",
                "request_owner": "ai_reviewer",
                "input_contract": {
                    "required_refs": {
                        "medical_prose_review": {"path": str(prose_review_path.resolve())},
                    }
                },
                "request_lifecycle": {
                    "state": "requested",
                    "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
                    "stale_record_ref": current_record_ref,
                    "required_currentness_refs": [str(prose_review_path.resolve())],
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(
        module.study_progress_projection,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": study_id,
            "quest_id": study_id,
            "study_root": str(study_root),
            "current_work_unit": {
                "status": "typed_blocker",
                "owner": "ai_reviewer",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::f11710a114497b27",
            },
        },
    )

    result = module.plan_ai_reviewer_publication_eval_record_materialization(
        profile=profile,
        study_id=study_id,
        study_root=None,
        entry_mode=None,
        source="cli",
        record={
            "surface": "ai_reviewer_record_payload_authoring_target",
            "stale_record_ref": stale_record_ref,
            "required_currentness_refs": [str(prose_review_path.resolve())],
            "required_input_refs": {"medical_prose_review": str(prose_review_path.resolve())},
            "record_payload": {
                "eval_id": "publication-eval::002::current",
                "reviewer_operating_system": {
                    "input_bundle": {
                        "medical_prose_review": str(prose_review_path.resolve()),
                    }
                },
            },
        },
        expected_owner="ai_reviewer",
        expected_action_type="run_quality_repair_batch",
        expected_work_unit_id="analysis_claim_evidence_repair",
        expected_work_unit_fingerprint="publication-blockers::f11710a114497b27",
    )

    assert result["status"] == "blocked"
    assert result["blocked_reason"] == "payload_currentness_mismatch"
    assert result["payload_guard"]["matched"] is False
    assert result["payload_guard"]["mismatches"] == [
        {"surface": "stale_record_ref", "expected": current_record_ref, "observed": stale_record_ref}
    ]
    assert result["written_files"] == []


def test_ai_reviewer_record_dry_run_plan_blocks_when_expected_identity_is_unavailable(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / study_id
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(
        json.dumps(
            {
                "study_id": study_id,
                "quest_id": study_id,
                "request_kind": "return_to_ai_reviewer_workflow",
                "request_owner": "ai_reviewer",
                "request_lifecycle": {"state": "requested"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module.study_progress_projection,
        "read_study_progress",
        lambda **kwargs: {"study_id": study_id, "quest_id": study_id, "study_root": str(study_root)},
    )

    result = module.plan_ai_reviewer_publication_eval_record_materialization(
        profile=profile,
        study_id=study_id,
        study_root=None,
        entry_mode=None,
        source="cli",
        expected_owner="ai_reviewer",
        expected_action_type="run_quality_repair_batch",
        expected_work_unit_id="analysis_claim_evidence_repair",
        expected_work_unit_fingerprint="publication-blockers::f11710a114497b27",
    )

    assert result["status"] == "blocked"
    assert result["blocked_reason"] == "current_owner_identity_unavailable_for_guard"
    assert result["identity_guard"]["matched"] is False
    assert result["identity_guard"]["missing_observed_fields"] == [
        "owner",
        "action_type",
        "work_unit_id",
        "work_unit_fingerprint",
    ]
    assert result["expected_current_work_unit"] == {
        "owner": "ai_reviewer",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "analysis_claim_evidence_repair",
        "work_unit_fingerprint": "publication-blockers::f11710a114497b27",
    }
    assert result["written_files"] == []


def test_ai_reviewer_record_dry_run_plan_fails_closed_on_expected_owner_mismatch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval")
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_id = "002-dm-china-us-mortality-attribution"
    write_profile(profile_path, workspace_root=workspace_root)
    profile = importlib.import_module("med_autoscience.profiles").load_profile(profile_path)
    study_root = workspace_root / "studies" / study_id
    request_path = study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json"
    request_path.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(
        json.dumps(
            {
                "study_id": study_id,
                "quest_id": study_id,
                "request_kind": "return_to_ai_reviewer_workflow",
                "request_owner": "ai_reviewer",
                "request_lifecycle": {"state": "requested"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        module.study_progress_projection,
        "read_study_progress",
        lambda **kwargs: {
            "study_id": study_id,
            "quest_id": study_id,
            "study_root": str(study_root),
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "analysis-campaign",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::f11710a114497b27",
            },
        },
    )

    matched_result = module.plan_ai_reviewer_publication_eval_record_materialization(
        profile=profile,
        study_id=study_id,
        study_root=None,
        entry_mode=None,
        source="cli",
        expected_owner="analysis-campaign",
        expected_action_type="run_quality_repair_batch",
        expected_work_unit_id="analysis_claim_evidence_repair",
        expected_work_unit_fingerprint="publication-blockers::f11710a114497b27",
    )
    mismatch_result = module.plan_ai_reviewer_publication_eval_record_materialization(
        profile=profile,
        study_id=study_id,
        study_root=None,
        entry_mode=None,
        source="cli",
        expected_owner="ai_reviewer",
        expected_action_type="run_quality_repair_batch",
        expected_work_unit_id="analysis_claim_evidence_repair",
        expected_work_unit_fingerprint="publication-blockers::f11710a114497b27",
    )

    assert matched_result["status"] == "dry_run"
    assert matched_result["identity_guard"]["matched"] is True
    assert matched_result["written_files"] == []
    assert mismatch_result["status"] == "blocked"
    assert mismatch_result["blocked_reason"] == "current_owner_identity_mismatch"
    assert mismatch_result["identity_guard"]["matched"] is False
    assert mismatch_result["identity_guard"]["mismatches"] == [
        {"field": "owner", "expected": "ai_reviewer", "observed": "analysis-campaign"}
    ]
    assert mismatch_result["identity_guard"]["missing_observed_fields"] == []
    assert mismatch_result["written_files"] == []
    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
    assert not (study_root / "artifacts" / "controller_decisions" / "latest.json").exists()
    assert not (study_root / "artifacts" / "publication_eval" / "ai_reviewer_responses").exists()
