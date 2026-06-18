from __future__ import annotations

from .shared import *  # noqa: F403,F401


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")


def test_stage_artifact_materialize_cli_dry_run_apply_and_idempotent_index(
    tmp_path: Path,
    capsys,
) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    domain_authority_refs_index = importlib.import_module(
        "med_autoscience.runtime_protocol.domain_authority_refs_index"
    )
    profile_path = tmp_path / "profile.local.toml"
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    write_profile(profile_path, workspace_root=workspace_root)
    _write_json(study_root / "study.yaml", {"study_id": "001-risk", "title": "Risk"})
    (study_root / "brief.md").write_text("question\n", encoding="utf-8")

    dry_run_exit = cli.main(
        [
            "stage-artifact-materialize",
            "--profile",
            str(profile_path),
            "--studies",
            "001-risk",
            "--stage-id",
            "01-study_intake",
            "--dry-run",
        ]
    )
    dry_run_payload = json.loads(capsys.readouterr().out)

    assert dry_run_exit == 0
    assert dry_run_payload["surface_kind"] == "stage_artifact_materialize_command"
    assert dry_run_payload["study_count"] == 1
    assert dry_run_payload["apply"] is False
    assert dry_run_payload["results"][0]["status"] == "dry_run"
    assert not (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "01-study_intake"
        / "receipts/owner_receipt.json"
    ).exists()

    apply_args = [
        "stage-artifact-materialize",
        "--profile",
        str(profile_path),
        "--studies",
        "001-risk",
        "--stage-id",
        "01-study_intake",
        "--apply",
    ]
    first_apply_exit = cli.main(apply_args)
    first_apply_payload = json.loads(capsys.readouterr().out)
    second_apply_exit = cli.main(apply_args)
    second_apply_payload = json.loads(capsys.readouterr().out)

    assert first_apply_exit == 0
    assert second_apply_exit == 0
    assert first_apply_payload["results"][0]["status"] == "materialized"
    assert second_apply_payload["results"][0]["status"] == "materialized"
    receipt_path = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "01-study_intake"
        / "receipts/owner_receipt.json"
    )
    assert receipt_path.is_file()
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["receipt_kind"] == "stage_artifact_delta"
    assert receipt["refs_only"] is True
    assert receipt["can_authorize_publication_ready"] is False

    index_result = first_apply_payload["results"][0]["stages"][0]["domain_authority_ref_index"]
    assert index_result["status"] == "source_adapter_emitted"
    assert index_result["indexed_table"] == "stage_artifact_delta_refs"
    assert index_result["sqlite_persisted"] is False
    assert index_result["opl_state_index_kernel_required"] is True
    sqlite_path = domain_authority_refs_index.workspace_authority_refs_index_path(workspace_root)
    inspection = domain_authority_refs_index.inspect_authority_refs_index(sqlite_path)
    assert inspection["status"] == "missing"
