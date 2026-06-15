from __future__ import annotations

import importlib
import json
from pathlib import Path

from med_autoscience import cli
from tests.study_runtime_test_helpers import make_profile, write_study, write_text


def _write_profile(path: Path, profile) -> None:
    path.write_text(
        "\n".join(
            [
                f'name = "{profile.name}"',
                f'workspace_root = "{profile.workspace_root}"',
                f'runtime_root = "{profile.runtime_root}"',
                f'studies_root = "{profile.studies_root}"',
                f'portfolio_root = "{profile.portfolio_root}"',
                f'med_deepscientist_runtime_root = "{profile.med_deepscientist_runtime_root}"',
                f'med_deepscientist_repo_root = "{profile.med_deepscientist_repo_root}"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "enable_medical_overlay = true",
                'medical_overlay_scope = "workspace"',
                'medical_overlay_skills = ["scout"]',
                'research_route_bias_policy = "high_plasticity_medical"',
                'preferred_study_archetypes = ["clinical_classifier"]',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_json(path: Path, payload: dict) -> None:
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _dispatch_payload(*, study_id: str, action_type: str, work_unit_id: str, fingerprint: str) -> dict:
    return {
        "surface": "default_executor_dispatch_request",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": action_type,
        "dispatch_status": "ready",
        "executor_kind": "codex_cli_default",
        "dispatch_authority": "consumer_default_executor_dispatch",
        "owner_route": {
            "next_owner": "gate_clearing_batch" if action_type == "run_gate_clearing_batch" else "write",
            "allowed_actions": [action_type],
            "source_refs": {
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
            },
            "work_unit_fingerprint": fingerprint,
        },
    }


def test_default_executor_dispatch_residue_cleanup_archives_only_mutable_stale_slots(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.default_executor_dispatch_residue_cleanup")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    dispatch_root = study_root / "artifacts" / "supervision" / "consumer" / "default_executor_dispatches"
    mutable = dispatch_root / "run_gate_clearing_batch.json"
    immutable = dispatch_root / "immutable" / "run_gate_clearing_batch" / "current.json"
    current_fingerprint = "sha256:6908b5fd4189779bc39fa7f869aeedd978159a73644c90b6ec2cf90b39d7a643"
    stale_fingerprint = "sha256:stale-dispatch-fingerprint"
    _write_json(
        mutable,
        _dispatch_payload(
            study_id=study_id,
            action_type="run_gate_clearing_batch",
            work_unit_id="publication_gate_replay",
            fingerprint=stale_fingerprint,
        ),
    )
    _write_json(
        immutable,
        _dispatch_payload(
            study_id=study_id,
            action_type="run_gate_clearing_batch",
            work_unit_id="publication_gate_replay",
            fingerprint=current_fingerprint,
        ),
    )
    _write_json(
        study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json",
        {"surface_kind": "gate_clearing_batch_owner_receipt", "status": "executed"},
    )

    def progress_reader(*, profile, study_id: str) -> dict:
        return {
            "study_id": study_id,
            "current_executable_owner_action": None,
            "current_work_unit": {
                "status": "owner_receipt_recorded",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": current_fingerprint,
                "required_output_contract": {
                    "owner_receipt_consumed": True,
                    "owner_receipt_ref": str(
                        study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
                    ),
                },
            },
            "paper_recovery_state": {
                "phase": "owner_receipt_recorded",
                "next_safe_action": {
                    "kind": "consume_owner_receipt",
                    "owner_receipt_ref": str(
                        study_root / "artifacts" / "controller" / "gate_clearing_batch" / "latest.json"
                    ),
                    "provider_admission_allowed": False,
                },
            },
        }

    dry_run = module.run_default_executor_dispatch_residue_cleanup(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=False,
        progress_reader=progress_reader,
    )

    assert dry_run["surface_kind"] == "default_executor_dispatch_residue_cleanup"
    assert dry_run["status"] == "cleanup_pending"
    assert dry_run["cleanup_candidate_count"] == 1
    assert dry_run["studies"][0]["ready_mutable_slot_count"] == 1
    assert dry_run["studies"][0]["stale_ready_mutable_slot_count"] == 1
    assert dry_run["studies"][0]["immutable_provenance_file_count"] == 1
    assert mutable.is_file()
    assert immutable.is_file()

    result = module.run_default_executor_dispatch_residue_cleanup(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=True,
        progress_reader=progress_reader,
    )

    assert result["status"] == "clean"
    assert result["post_apply"]["remaining_cleanup_candidate_count"] == 0
    assert not mutable.exists()
    assert immutable.is_file()
    archived = result["studies"][0]["archived_mutable_slots"][0]
    archived_path = Path(archived["archive_absolute_path"])
    assert archived_path.is_file()
    assert archived["source_sha256"].startswith("sha256:")
    receipt_path = study_root / "artifacts" / "migration" / "default_executor_dispatch_residue_cleanup" / "latest.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["status"] == "applied"
    assert receipt["authority_boundary"]["immutable_dispatch_provenance_mutation"] is False
    assert receipt["studies"][0]["archived_mutable_slots"][0]["source_relative_path"].endswith(
        "default_executor_dispatches/run_gate_clearing_batch.json"
    )


def test_default_executor_dispatch_residue_cleanup_fail_closed_when_current_action_exists(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.default_executor_dispatch_residue_cleanup")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    study_id = "002-dm-china-us-mortality-attribution"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    mutable = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_json(
        mutable,
        _dispatch_payload(
            study_id=study_id,
            action_type="run_quality_repair_batch",
            work_unit_id="medical_prose_write_repair",
            fingerprint="publication-blockers::0915410f804b3697",
        ),
    )

    def progress_reader(*, profile, study_id: str) -> dict:
        return {
            "study_id": study_id,
            "current_executable_owner_action": {
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            },
            "current_work_unit": {
                "status": "executable_owner_action",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            },
            "paper_recovery_state": {
                "phase": "provider_admission_pending",
                "next_safe_action": {"kind": "admit_provider_attempt", "provider_admission_allowed": True},
            },
        }

    result = module.run_default_executor_dispatch_residue_cleanup(
        profile_path=profile_path,
        study_ids=(study_id,),
        apply=False,
        progress_reader=progress_reader,
    )

    assert result["status"] == "typed_blocked"
    assert result["cleanup_candidate_count"] == 0
    assert result["studies"][0]["blockers"][0]["reason"] == "current_executable_owner_action_present"
    assert mutable.is_file()


def test_default_executor_dispatch_residue_cleanup_default_reader_uses_study_progress(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.default_executor_dispatch_residue_cleanup")
    profile = make_profile(tmp_path)
    seen: dict[str, object] = {}

    def read_study_progress(**kwargs) -> dict:
        seen.update(kwargs)
        return {
            "study_id": kwargs["study_id"],
            "current_work_unit": {"status": "typed_blocker", "work_unit_id": "blocked-unit"},
            "paper_recovery_state": {
                "phase": "domain_blocked",
                "next_safe_action": {"kind": "resolve_typed_blocker"},
            },
        }

    monkeypatch.setattr(module.study_progress, "read_study_progress", read_study_progress)

    result = module._default_progress_reader(profile=profile, study_id="002-risk")

    assert result["current_work_unit"]["status"] == "typed_blocker"
    assert result["paper_recovery_state"]["next_safe_action"]["kind"] == "resolve_typed_blocker"
    assert seen == {
        "profile": profile,
        "profile_ref": None,
        "study_id": "002-risk",
        "entry_mode": None,
        "sync_runtime_summary": False,
        "materialize_read_model_artifacts": False,
    }


def test_default_executor_dispatch_residue_cleanup_cli_dispatches_json(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    profile_path = tmp_path / "profile.local.toml"
    called = {}

    def fake_run_default_executor_dispatch_residue_cleanup(*, profile_path, study_ids, apply):
        called["profile_path"] = Path(profile_path)
        called["study_ids"] = study_ids
        called["apply"] = apply
        return {
            "surface_kind": "default_executor_dispatch_residue_cleanup",
            "status": "clean",
            "study_count": len(study_ids),
        }

    monkeypatch.setattr(
        cli.default_executor_dispatch_residue_cleanup,
        "run_default_executor_dispatch_residue_cleanup",
        fake_run_default_executor_dispatch_residue_cleanup,
    )

    exit_code = cli.main(
        [
            "default-executor-dispatch-residue-cleanup",
            "--profile",
            str(profile_path),
            "--studies",
            "dm002",
            "dm003",
            "--apply",
        ]
    )
    payload = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert called == {"profile_path": profile_path, "study_ids": ("dm002", "dm003"), "apply": True}
    assert payload["surface_kind"] == "default_executor_dispatch_residue_cleanup"
    assert payload["status"] == "clean"
