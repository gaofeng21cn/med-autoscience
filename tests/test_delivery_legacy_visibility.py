from __future__ import annotations

import importlib
from pathlib import Path

from tests.test_delivery_inspector import _write_profile_for_workspace
from tests.test_study_delivery_sync_cases.shared import dump_json, make_delivery_workspace, write_text
from tests.control_plane_route_helpers import writable_route_context


def _legacy_inspection() -> dict:
    return {
        "surface": "delivery_inspector",
        "study_id": "001-legacy",
        "freshness": {"verdict": "legacy", "delivery_status": "current"},
        "source_package": {
            "role": "controller_authorized_source",
            "root": "/workspace/studies/001/paper/submission_minimal",
            "exists": True,
            "layout_status": "legacy",
            "audit_completeness": {"status": "missing"},
            "reproducibility_completeness": {"status": "missing"},
            "legacy_root_file_status": {"status": "present", "present": ["submission_manifest"]},
        },
        "human_package": {
            "role": "human_facing_mirror",
            "root": "/workspace/studies/001/manuscript/current_package",
            "exists": True,
            "layout_status": "legacy",
            "audit_completeness": {"status": "missing"},
            "reproducibility_completeness": {"status": "missing"},
            "legacy_root_file_status": {"status": "present", "present": ["submission_manifest"]},
        },
        "zip": {
            "path": "/workspace/studies/001/manuscript/current_package.zip",
            "exists": True,
            "root_audit_entries": ["submission_manifest.json"],
        },
        "next_sync_command": "medautosci study delivery-sync --paper-root /workspace/studies/001/paper --stage submission_minimal",
    }


def test_delivery_legacy_visibility_projects_legacy_queue_and_read_only_authority() -> None:
    module = importlib.import_module("med_autoscience.controllers.delivery_legacy_visibility")

    read_model = module.build_delivery_legacy_visibility_read_model(_legacy_inspection())

    assert read_model["read_model"] == "delivery_legacy_visibility_read_model"
    assert read_model["projection_only"] is True
    assert read_model["traffic_light"]["status"] == "legacy_pending"
    assert len(read_model["legacy_upgrade_queue"]) == 3
    assert read_model["legacy_upgrade_queue"][0]["next_action"] == "run_controller_authorized_delivery_sync"
    assert [item["section"] for item in read_model["doctor_readme_structure_projection"]] == [
        "Submission files",
        "Audit and reproducibility",
        "Delivery status",
        "Next controller-authorized sync",
    ]
    assert all(item["editable_source"] is False for item in read_model["doctor_readme_structure_projection"])
    assert read_model["backfill_blocker_report"]["status"] == "blocked"
    assert read_model["backfill_blocker_report"]["blocker_count"] >= 3
    assert read_model["authority"] == {
        "mode": "read_model/projection_only",
        "projection_only": True,
        "can_write_delivery_truth": False,
        "write_authority": "controller_authorized_delivery_sync_apply_only",
    }


def test_delivery_legacy_visibility_traffic_light_current_stale_and_missing() -> None:
    module = importlib.import_module("med_autoscience.controllers.delivery_legacy_visibility")
    current = {
        "freshness": {"verdict": "current", "delivery_status": "current"},
        "source_package": {"exists": True, "layout_status": "v2"},
        "human_package": {"exists": True, "layout_status": "v2"},
    }
    stale = {
        **current,
        "freshness": {"verdict": "stale", "delivery_status": "stale_source_changed"},
    }
    missing = {
        **current,
        "freshness": {"verdict": "missing", "delivery_status": "missing"},
        "human_package": {"exists": False, "layout_status": "missing"},
    }

    assert module.build_delivery_legacy_visibility_read_model(current)["traffic_light"]["status"] == "current"
    stale_model = module.build_delivery_legacy_visibility_read_model(stale)
    assert stale_model["traffic_light"]["status"] == "stale"
    assert stale_model["backfill_blocker_report"]["blockers"][0]["blocker_id"] == "delivery_stale"
    missing_model = module.build_delivery_legacy_visibility_read_model(missing)
    assert missing_model["traffic_light"]["status"] == "missing"
    assert any(
        blocker["blocker_id"] == "human_package_missing"
        for blocker in missing_model["backfill_blocker_report"]["blockers"]
    )


def test_delivery_visibility_projection_embeds_l4_read_model() -> None:
    projection_module = importlib.import_module("med_autoscience.controllers.delivery_visibility_projection")

    projection = projection_module.compact_delivery_inspection_projection(_legacy_inspection())

    assert projection["status"] == "legacy_layout_pending_sync"
    assert projection["read_model"] == "delivery_visibility_projection"
    assert projection["projection_only"] is True
    assert projection["legacy_visibility"]["traffic_light"]["status"] == "legacy_pending"
    assert projection["legacy_visibility"]["authority"]["can_write_delivery_truth"] is False
    markdown = "\n".join(
        projection_module.render_delivery_inspection_markdown_lines(
            projection,
            heading="## Delivery Inspection",
        )
    )
    assert "delivery traffic-light: `legacy_pending`" in markdown
    assert "legacy upgrade queue: `3` item(s)" in markdown
    assert "backfill blockers: `blocked`" in markdown


def test_inspect_delivery_legacy_visibility_reads_real_delivery_without_writing_truth(tmp_path: Path) -> None:
    sync_module = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    profiles = importlib.import_module("med_autoscience.profiles")
    module = importlib.import_module("med_autoscience.controllers.delivery_legacy_visibility")
    paper_root, study_root = make_delivery_workspace(tmp_path)
    profile_path = tmp_path / "profile.local.toml"
    _write_profile_for_workspace(profile_path, workspace_root=tmp_path / "repo")
    sync_module.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
        route_context=writable_route_context(),
    )

    read_model = module.inspect_delivery_legacy_visibility(
        profile=profiles.load_profile(profile_path),
        profile_ref=profile_path,
        study_id=study_root.name,
    )

    assert read_model["traffic_light"]["status"] == "current"
    assert read_model["legacy_upgrade_queue"] == []
    assert read_model["backfill_blocker_report"]["status"] == "clear"
    assert read_model["authority"]["can_write_delivery_truth"] is False


def test_inspect_delivery_legacy_visibility_reports_legacy_backfill_without_mutation(tmp_path: Path) -> None:
    profiles = importlib.import_module("med_autoscience.profiles")
    module = importlib.import_module("med_autoscience.controllers.delivery_legacy_visibility")
    workspace_root = tmp_path / "repo"
    study_root = workspace_root / "studies" / "001-legacy-delivery"
    source_root = study_root / "paper" / "submission_minimal"
    human_root = study_root / "manuscript" / "current_package"
    profile_path = tmp_path / "profile.local.toml"
    _write_profile_for_workspace(profile_path, workspace_root=workspace_root)
    write_text(study_root / "study.yaml", "study_id: 001-legacy-delivery\n")
    write_text(source_root / "manuscript.docx", "docx")
    write_text(source_root / "paper.pdf", "%PDF-1.4\n")
    dump_json(source_root / "submission_manifest.json", {"schema_version": 1})
    write_text(human_root / "manuscript.docx", "docx")
    write_text(human_root / "paper.pdf", "%PDF-1.4\n")
    dump_json(human_root / "submission_manifest.json", {"schema_version": 1})

    read_model = module.inspect_delivery_legacy_visibility(
        profile=profiles.load_profile(profile_path),
        profile_ref=profile_path,
        study_id=study_root.name,
    )

    assert read_model["traffic_light"]["status"] == "legacy_pending"
    assert read_model["legacy_upgrade_queue"]
    assert read_model["backfill_blocker_report"]["status"] == "blocked"
    assert not (source_root / "audit").exists()
    assert not (human_root / "audit").exists()
