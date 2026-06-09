from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import make_profile, write_text


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
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_legacy_ds_retirement_apply_archives_and_removes_all_ds_roots(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.legacy_ds_retirement")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    quest_root = profile.runtime_root / "quest-clean"
    write_text(quest_root / "quest.yaml", "quest_id: quest-clean\nstudy_id: 001-clean\n")
    _write_json(quest_root / ".ds" / "runtime_state.json", {"quest_id": "quest-clean", "status": "paused"})
    write_text(quest_root / ".ds" / "events.jsonl", '{"event":"legacy"}\n')
    write_text(quest_root / ".ds" / "interaction_journal.jsonl", '{"turn":"legacy"}\n')
    _write_json(quest_root / ".ds" / "user_message_queue.json", {"pending": [], "completed": []})
    archive_owner = profile.workspace_root / "runtime" / "archives" / "legacy_mds" / "snapshot" / "runtime" / "quests" / "old"
    write_text(archive_owner / ".ds" / "runtime_state.json", '{"status":"completed"}\n')

    dry_run = module.run_legacy_ds_retirement(profile_path=profile_path, apply=False)

    assert dry_run["status"] == "planned"
    assert dry_run["ds_root_count"] == 2
    assert dry_run["all_ds_removed"] is False
    assert (quest_root / ".ds" / "runtime_state.json").is_file()

    result = module.run_legacy_ds_retirement(profile_path=profile_path, apply=True)

    assert result["status"] == "retired"
    assert result["ds_root_count"] == 2
    assert result["retired_count"] == 2
    assert result["all_ds_removed"] is True
    assert not (quest_root / ".ds").exists()
    assert not (archive_owner / ".ds").exists()
    canonical_state = quest_root / "artifacts" / "runtime" / "state" / "runtime_state.json"
    assert json.loads(canonical_state.read_text(encoding="utf-8"))["status"] == "paused"
    latest = json.loads(
        (profile.workspace_root / "runtime" / "artifacts" / "legacy_ds_retirement" / "latest.json").read_text(
            encoding="utf-8"
        )
    )
    assert latest["status"] == "retired"
    assert latest["all_ds_removed"] is True
    for entry in latest["retired"]:
        archive_path = Path(entry["archive_path"])
        manifest_path = Path(entry["source_manifest_path"])
        proof_path = Path(entry["restore_proof_path"])
        receipt_path = Path(entry["receipt_path"])
        assert archive_path.is_file()
        assert manifest_path.is_file()
        assert json.loads(proof_path.read_text(encoding="utf-8"))["status"] == "verified"
        assert json.loads(receipt_path.read_text(encoding="utf-8"))["legacy_ds_removed"] is True


def test_legacy_ds_retirement_treats_nested_ds_as_parent_payload(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.legacy_ds_retirement")
    profile = make_profile(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile(profile_path, profile)
    quest_root = profile.runtime_root / "quest-with-nested-ds"
    write_text(quest_root / "quest.yaml", "quest_id: quest-with-nested-ds\n")
    write_text(quest_root / ".ds" / "python_pycache" / "inner" / ".ds" / "runs" / "run-a" / "stdout.jsonl", "nested\n")

    dry_run = module.run_legacy_ds_retirement(profile_path=profile_path, apply=False)

    assert dry_run["ds_root_count"] == 1
    assert dry_run["planned"][0]["ds_root"] == str((quest_root / ".ds").resolve())

    result = module.run_legacy_ds_retirement(profile_path=profile_path, apply=True)

    assert result["status"] == "retired"
    assert result["ds_root_count"] == 1
    assert result["all_ds_removed"] is True
    assert not (quest_root / ".ds").exists()


def test_legacy_ds_retirement_cli_dispatches_controller(monkeypatch, tmp_path: Path, capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")
    profile_path = tmp_path / "profile.local.toml"
    profile_path.write_text('name = "test"\nworkspace_root = "/tmp/workspace"\n', encoding="utf-8")
    called: dict[str, object] = {}

    def fake_run_legacy_ds_retirement(*, profile_path: Path, apply: bool) -> dict[str, object]:
        called["profile_path"] = profile_path
        called["apply"] = apply
        return {"surface_kind": "legacy_ds_retirement", "status": "retired"}

    monkeypatch.setattr(cli.legacy_ds_retirement, "run_legacy_ds_retirement", fake_run_legacy_ds_retirement)

    exit_code = cli.main(["runtime", "legacy-ds-retire", "--profile", str(profile_path), "--apply"])

    assert exit_code == 0
    assert called == {"profile_path": profile_path, "apply": True}
    assert json.loads(capsys.readouterr().out)["surface_kind"] == "legacy_ds_retirement"
