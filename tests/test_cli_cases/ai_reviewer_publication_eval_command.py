from __future__ import annotations

from . import shared as _shared
from .ai_reviewer_publication_eval_command_cases.test_identity_guard_cases import *  # noqa: F401,F403
from .ai_reviewer_publication_eval_command_cases.test_payload_currentness_refs_cases import *  # noqa: F401,F403
from .ai_reviewer_publication_eval_command_cases.test_payload_currentness_guard_cases import *  # noqa: F401,F403
from .ai_reviewer_publication_eval_command_cases.test_payload_schema_and_trace_cases import *  # noqa: F401,F403

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
    assert called["build_production_trace"] is False
    assert json.loads(captured.out)["assessment_owner"] == "ai_reviewer"


def test_publication_ai_reviewer_eval_command_can_request_production_trace_rebuild(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
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
        build_production_trace: bool = False,
    ) -> dict:
        called["build_production_trace"] = build_production_trace
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
            "--build-production-trace",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["build_production_trace"] is True
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
        authoring_target_output: Path | None = None,
        build_production_trace: bool = False,
    ) -> dict:
        called["precheck"] = True
        called["precheck_record"] = record
        called["expected_owner"] = expected_owner
        called["expected_action_type"] = expected_action_type
        called["expected_work_unit_id"] = expected_work_unit_id
        called["expected_work_unit_fingerprint"] = expected_work_unit_fingerprint
        called["authoring_target_output"] = authoring_target_output
        called["build_production_trace"] = build_production_trace
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
        authoring_target_output: Path | None = None,
        build_production_trace: bool = False,
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
        called["authoring_target_output"] = authoring_target_output
        called["build_production_trace"] = build_production_trace
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
    assert called["build_production_trace"] is True
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
