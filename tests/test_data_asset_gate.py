from __future__ import annotations

import importlib
import json
from pathlib import Path


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_workspace_with_quest(tmp_path: Path, *, study_id: str = "002-early-residual-risk") -> tuple[Path, Path]:
    workspace_root = tmp_path / "workspace"
    quest_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / study_id
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": study_id,
            "status": "running",
            "active_run_id": "run-1",
        },
    )
    (quest_root / "quest.yaml").write_text(f"quest_id: {study_id}\n", encoding="utf-8")
    (workspace_root / "studies" / study_id).mkdir(parents=True, exist_ok=True)
    (workspace_root / "studies" / study_id / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    return workspace_root, quest_root


def write_dataset_manifest(path: Path, *, dataset_id: str, relative_path: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "dataset_inputs:",
                f"  - dataset_id: {dataset_id}",
                f"    path: {relative_path}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_build_gate_report_blocks_when_private_release_is_outdated(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_asset_gate")
    workspace_root, quest_root = make_workspace_with_quest(tmp_path)
    (workspace_root / "datasets" / "master" / "v2026-03-28").mkdir(parents=True, exist_ok=True)
    (workspace_root / "datasets" / "master" / "v2026-04-10").mkdir(parents=True, exist_ok=True)
    (workspace_root / "datasets" / "master" / "v2026-03-28" / "analysis.csv").write_text("id\n1\n", encoding="utf-8")
    (workspace_root / "datasets" / "master" / "v2026-04-10" / "analysis.csv").write_text("id\n1\n2\n", encoding="utf-8")
    write_dataset_manifest(
        workspace_root / "studies" / "002-early-residual-risk" / "data_input" / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        relative_path="../../../datasets/master/v2026-03-28/analysis.csv",
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "outdated_private_release" in report["blockers"]
    assert report["study_id"] == "002-early-residual-risk"


def test_build_gate_report_blocks_when_private_contract_is_unresolved(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_asset_gate")
    workspace_root, quest_root = make_workspace_with_quest(tmp_path)
    version_root = workspace_root / "datasets" / "master" / "v2026-03-28"
    version_root.mkdir(parents=True, exist_ok=True)
    (version_root / "analysis.csv").write_text("id\n1\n", encoding="utf-8")
    write_dataset_manifest(
        workspace_root / "studies" / "002-early-residual-risk" / "data_input" / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        relative_path="../../../datasets/master/v2026-03-28/analysis.csv",
    )

    state = module.build_gate_state(quest_root)
    report = module.build_gate_report(state)

    assert report["status"] == "blocked"
    assert "unresolved_private_data_contract" in report["blockers"]
    assert report["unresolved_dataset_ids"] == ["nfpitnet_master"]


def test_run_controller_enqueues_advisory_message_when_public_extension_available(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_asset_gate")
    workspace_root, quest_root = make_workspace_with_quest(tmp_path)
    version_root = workspace_root / "datasets" / "master" / "v2026-03-28"
    version_root.mkdir(parents=True, exist_ok=True)
    (version_root / "analysis.csv").write_text("id\n1\n", encoding="utf-8")
    (version_root / "dataset_manifest.yaml").write_text(
        "\n".join(
            [
                "dataset_id: nfpitnet_master",
                "version: v2026-03-28",
                "raw_snapshot: baseline",
                "generated_by: pipeline/v1.py",
                "main_outputs:",
                "  analysis_csv: analysis.csv",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    write_dataset_manifest(
        workspace_root / "studies" / "002-early-residual-risk" / "data_input" / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        relative_path="../../../datasets/master/v2026-03-28/analysis.csv",
    )
    dump_json(
        workspace_root / "portfolio" / "data_assets" / "public" / "registry.json",
        {
            "schema_version": 2,
            "datasets": [
                {
                    "dataset_id": "geo-gse000001",
                    "source_type": "GEO",
                    "accession": "GSE000001",
                    "roles": ["external_validation"],
                    "target_families": ["master"],
                    "target_dataset_ids": ["nfpitnet_master"],
                    "status": "candidate",
                    "rationale": "Can be used for external validation.",
                }
            ],
        },
    )

    result = module.run_controller(quest_root=quest_root, apply=True)

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    assert result["status"] == "advisory"
    assert result["blockers"] == []
    assert result["advisories"] == ["public_data_extension_available"]
    assert result["intervention_enqueued"] is True
    assert len(queue["pending"]) == 1
    assert "public-data extension" in queue["pending"][0]["content"]
    assert "do not need to stop the current run" in queue["pending"][0]["content"]


def test_run_controller_reports_unresolved_dataset_ids_in_hard_block_message(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_asset_gate")
    workspace_root, quest_root = make_workspace_with_quest(tmp_path)
    version_root = workspace_root / "datasets" / "master" / "v2026-03-28"
    version_root.mkdir(parents=True, exist_ok=True)
    (version_root / "analysis.csv").write_text("id\n1\n", encoding="utf-8")
    write_dataset_manifest(
        workspace_root / "studies" / "002-early-residual-risk" / "data_input" / "dataset_manifest.yaml",
        dataset_id="nfpitnet_master",
        relative_path="../../../datasets/master/v2026-03-28/analysis.csv",
    )

    result = module.run_controller(quest_root=quest_root, apply=True)

    queue = json.loads((quest_root / ".ds" / "user_message_queue.json").read_text(encoding="utf-8"))
    assert result["status"] == "blocked"
    assert result["unresolved_dataset_ids"] == ["nfpitnet_master"]
    assert "nfpitnet_master" in queue["pending"][0]["content"]


def test_build_gate_state_uses_runtime_protocol_quest_state(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_asset_gate")
    workspace_root = tmp_path / "workspace"
    study_id = "002-early-residual-risk"
    quest_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / study_id
    (quest_root / "quest.yaml").parent.mkdir(parents=True, exist_ok=True)
    (quest_root / "quest.yaml").write_text(f"quest_id: {study_id}\n", encoding="utf-8")
    (workspace_root / "studies" / study_id).mkdir(parents=True, exist_ok=True)
    (workspace_root / "studies" / study_id / "study.yaml").write_text(f"study_id: {study_id}\n", encoding="utf-8")
    seen: dict[str, object] = {}

    def fake_load_runtime_state(path: Path) -> dict[str, object]:
        seen["quest_root"] = path
        return {"status": "patched", "quest_id": study_id}

    monkeypatch.setattr(module.quest_state, "load_runtime_state", fake_load_runtime_state)
    monkeypatch.setattr(
        module.data_assets,
        "assess_data_asset_impact",
        lambda *, workspace_root: {"studies": [{"study_id": study_id, "status": "clear", "dataset_inputs": []}]},
    )

    state = module.build_gate_state(quest_root)

    assert seen == {"quest_root": quest_root}
    assert state.runtime_state["status"] == "patched"


def test_write_gate_files_uses_runtime_protocol_report_store(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.data_asset_gate")
    _, quest_root = make_workspace_with_quest(tmp_path)
    seen: dict[str, object] = {}

    def fake_write_timestamped_report(
        *,
        quest_root: Path,
        report_group: str,
        timestamp: str,
        report: dict[str, object],
        markdown: str,
    ) -> tuple[Path, Path]:
        seen["quest_root"] = quest_root
        seen["report_group"] = report_group
        seen["timestamp"] = timestamp
        seen["report"] = report
        seen["markdown"] = markdown
        return quest_root / "artifacts" / "reports" / report_group / "latest.json", quest_root / "artifacts" / "reports" / report_group / "latest.md"

    monkeypatch.setattr(module.runtime_protocol_report_store, "write_timestamped_report", fake_write_timestamped_report)

    report = {
        "generated_at": "2026-04-03T04:10:00+00:00",
        "study_id": quest_root.name,
        "status": "blocked",
        "recommended_action": "stop",
        "blockers": ["outdated_private_release"],
        "advisories": [],
        "study_status": "blocked",
        "outdated_dataset_ids": ["nfpitnet_master"],
        "public_support_dataset_ids": [],
        "controller_note": "note",
    }

    json_path, md_path = module.write_gate_files(quest_root, report)

    assert seen["quest_root"] == quest_root
    assert seen["report_group"] == "data_asset_gate"
    assert seen["timestamp"] == "2026-04-03T04:10:00+00:00"
    assert json_path.name == "latest.json"
    assert md_path.name == "latest.md"
