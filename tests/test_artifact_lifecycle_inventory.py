from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write(path: Path, text: str = "payload\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_artifact_inventory_classifies_roles_and_lifecycle(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_inventory")
    study_root = tmp_path / "studies" / "001-risk"
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"

    paths_by_expected_role = {
        "canonical_source": _write(study_root / "paper" / "source" / "manuscript_source.md"),
        "runtime_ephemeral": _write(quest_root / ".ds" / "runs" / "run-001" / "stdout.jsonl"),
        "derived_projection": _write(study_root / "manuscript" / "current_package" / "manuscript.docx"),
        "human_handoff_mirror": _write(study_root / "manuscript" / "README.md"),
        "data_release": _write(tmp_path / "datasets" / "master" / "v1" / "dataset_manifest.yaml"),
        "cold_archive": _write(quest_root / ".ds" / "cold_archive" / "worktree_runtime_payloads" / "run.tar.gz"),
        "audit_log": _write(study_root / "artifacts" / "runtime" / "runtime_storage_maintenance" / "latest.json"),
    }

    inventory = module.build_artifact_lifecycle_inventory(
        study_root=study_root,
        quest_root=quest_root,
        paths=tuple(paths_by_expected_role.values()),
    )

    by_path = {Path(item["path"]): item for item in inventory["artifacts"]}
    assert {item["role"] for item in inventory["artifacts"]} == set(paths_by_expected_role)
    assert by_path[paths_by_expected_role["canonical_source"]]["lifecycle"] == "active_authority"
    assert by_path[paths_by_expected_role["runtime_ephemeral"]]["lifecycle"] == "runtime_transient"
    assert by_path[paths_by_expected_role["derived_projection"]]["lifecycle"] == "rebuildable_projection"
    assert by_path[paths_by_expected_role["human_handoff_mirror"]]["lifecycle"] == "human_handoff"
    assert by_path[paths_by_expected_role["data_release"]]["lifecycle"] == "retained_release"
    assert by_path[paths_by_expected_role["cold_archive"]]["lifecycle"] == "archived_restore_candidate"
    assert by_path[paths_by_expected_role["audit_log"]]["lifecycle"] == "audit_retained"


def test_artifact_lifecycle_authority_kernel_prefers_manifest_owner_and_keeps_suffix_as_subtype(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_authority_kernel")
    study_root = tmp_path / "studies" / "001-risk"
    raw_release_zip = _write(study_root / "paper" / "raw" / "restricted" / "release.zip", "zip\n")

    artifact = module.ArtifactLifecycleAuthorityKernel(
        study_root=study_root,
        manifest={
            "artifacts": [
                {
                    "path": str(raw_release_zip),
                    "owner": "data_steward",
                    "source_refs": {"intake_manifest": "inbox/release_manifest.json"},
                    "fingerprint": "sha256:raw-release",
                }
            ]
        },
    ).classify(raw_release_zip)

    assert artifact["role"] == "data_release"
    assert artifact["lifecycle"] == "raw_intake"
    assert artifact["owner"] == "data_steward"
    assert artifact["subtype"] == "zip"
    assert artifact["source_refs"] == {"intake_manifest": "inbox/release_manifest.json"}
    assert artifact["fingerprint"] == "sha256:raw-release"
    assert artifact["authority_allowed"] == {"edit": False, "quality": False, "dispatch": False}


def test_artifact_inventory_treats_inbox_and_dataset_zip_as_raw_intake_not_delivery_projection(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_inventory")
    study_root = tmp_path / "studies" / "001-risk"
    inbox_zip = _write(tmp_path / "inbox" / "source_extract.zip", "zip\n")
    dataset_zip = _write(tmp_path / "datasets" / "master" / "v1" / "source_extract.zip", "zip\n")

    inventory = module.build_artifact_lifecycle_inventory(
        study_root=study_root,
        paths=(inbox_zip, dataset_zip),
    )

    by_path = {Path(item["path"]): item for item in inventory["artifacts"]}
    for raw_path in (inbox_zip, dataset_zip):
        artifact = by_path[raw_path.resolve()]
        assert artifact["role"] == "data_release"
        assert artifact["lifecycle"] == "raw_intake"
        assert artifact["subtype"] == "zip"
        assert artifact["authority_allowed"] == {"edit": False, "quality": False, "dispatch": False}
        assert artifact["edit_source_allowed"] is False
        assert artifact["quality_authority_allowed"] is False
        assert artifact["dispatch_authority_allowed"] is False


def test_study_artifact_registry_discovers_surfaces_and_blocks_generated_authority(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_inventory")
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    quest_root = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "001-risk"

    canonical_source = _write(study_root / "paper" / "source" / "manuscript_source.md")
    submission_docx = _write(study_root / "paper" / "submission_minimal" / "manuscript.docx")
    submission_pdf = _write(study_root / "paper" / "submission_minimal" / "paper.pdf")
    current_package_docx = _write(study_root / "manuscript" / "current_package" / "manuscript.docx")
    current_package_zip = _write(study_root / "manuscript" / "current_package.zip", "zip\n")
    runtime_log = _write(quest_root / ".ds" / "runs" / "run-live" / "stdout.jsonl")
    cold_archive = _write(quest_root / ".ds" / "cold_archive" / "payload.tar.gz")
    audit_log = _write(study_root / "artifacts" / "runtime" / "latest.json")
    data_manifest = _write(workspace_root / "datasets" / "master" / "v1" / "dataset_manifest.yaml")

    registry = module.build_study_artifact_lifecycle_registry(
        study_root=study_root,
        quest_root=quest_root,
        workspace_root=workspace_root,
        runtime_status={"status": "running", "active_run_id": "run-live"},
    )

    by_path = {Path(item["path"]): item for item in registry["artifacts"]}
    assert registry["surface_kind"] == "workspace_study_artifact_lifecycle_registry"
    assert set(registry["summary"]["role_counts"]) == set(module.ARTIFACT_ROLES)
    assert by_path[canonical_source.resolve()]["role"] == "canonical_source"
    assert by_path[runtime_log.resolve()]["cleanup_candidate_action"] == "audit-only"
    assert by_path[cold_archive.resolve()]["role"] == "cold_archive"
    assert by_path[audit_log.resolve()]["role"] == "audit_log"
    assert by_path[data_manifest.resolve()]["role"] == "data_release"
    for generated_path in (submission_docx, submission_pdf, current_package_docx, current_package_zip):
        artifact = by_path[generated_path.resolve()]
        assert artifact["role"] == "derived_projection"
        assert artifact["edit_source_allowed"] is False
        assert artifact["quality_authority_allowed"] is False
        assert artifact["dispatch_authority_allowed"] is False
        assert artifact["authority_blockers"] == [
            "generated_delivery_surface_cannot_be_edit_source",
            "generated_delivery_surface_cannot_be_quality_authority",
            "generated_delivery_surface_cannot_be_dispatch_authority",
        ]


def test_artifact_inventory_projects_mds_package_locator_signal_as_request_only(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_inventory")
    study_root = tmp_path / "studies" / "001-risk"
    current_package_docx = _write(study_root / "manuscript" / "current_package" / "manuscript.docx")
    current_package_zip = _write(study_root / "manuscript" / "current_package.zip", "zip\n")

    inventory = module.build_artifact_lifecycle_inventory(
        study_root=study_root,
        paths=(current_package_docx, current_package_zip),
        mds_mechanical_signals={
            "package_locator": {
                "status": "pass",
                "current_package_found": True,
                "requested_ready_state": "submission_ready",
            }
        },
    )

    assert inventory["mds_mechanical_signal_contract"] == {
        "role": "evidence_only",
        "mechanical_signal_can_only": "request_artifact_or_package_review",
        "quality_ready_authorized": False,
        "publication_ready_authorized": False,
        "submission_ready_authorized": False,
    }
    assert inventory["summary"]["mds_signal_request_count"] == 1
    assert inventory["summary"]["ready_authorization_count"] == 0
    assert inventory["mds_mechanical_requests"] == [
        {
            "signal_id": "package_locator",
            "request_kind": "artifact_or_package_review",
            "status": "pass",
            "quality_ready_authorized": False,
            "publication_ready_authorized": False,
            "submission_ready_authorized": False,
        }
    ]
    for artifact in inventory["artifacts"]:
        assert artifact["quality_authority_allowed"] is False
        assert artifact["dispatch_authority_allowed"] is False


def test_delivery_authority_sync_blocks_generated_surfaces_as_edit_or_quality_authority(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_inventory")
    study_root = tmp_path / "studies" / "001-risk"
    generated_paths = (
        _write(study_root / "manuscript" / "current_package" / "manuscript.docx"),
        _write(study_root / "manuscript" / "current_package.zip", "zip\n"),
        _write(study_root / "paper" / "submission_minimal" / "paper.pdf", "%PDF\n"),
        _write(study_root / "paper" / "submission_minimal" / "manuscript.docx"),
    )

    sync = module.build_delivery_authority_sync(study_root=study_root, paths=generated_paths)

    assert sync["status"] == "projection_only"
    assert sync["direct_edit_allowed"] is False
    assert sync["quality_authority_allowed"] is False
    assert sync["dispatch_authority_allowed"] is False
    assert sync["blocked_authority_paths"] == [str(path.resolve()) for path in generated_paths]
    assert sync["authority_source_roles"] == ["canonical_source"]
    assert sync["blocked_dispatch_paths"] == [str(path.resolve()) for path in generated_paths]


def test_docx_pdf_and_zip_outputs_are_projection_only_even_outside_named_delivery_roots(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_inventory")
    study_root = tmp_path / "studies" / "001-risk"
    generated_outputs = (
        _write(study_root / "paper" / "build" / "manuscript.docx"),
        _write(study_root / "paper" / "build" / "paper.pdf", "%PDF\n"),
        _write(study_root / "paper" / "build" / "submission_package.zip", "zip\n"),
    )

    inventory = module.build_artifact_lifecycle_inventory(
        study_root=study_root,
        paths=generated_outputs,
    )

    by_path = {Path(item["path"]): item for item in inventory["artifacts"]}
    for generated_path in generated_outputs:
        artifact = by_path[generated_path.resolve()]
        assert artifact["role"] == "derived_projection"
        assert artifact["lifecycle"] == "rebuildable_projection"
        assert artifact["authority_allowed"] == {"edit": False, "quality": False, "dispatch": False}
        assert artifact["edit_source_allowed"] is False
        assert artifact["quality_authority_allowed"] is False
        assert artifact["dispatch_authority_allowed"] is False
        assert artifact["authority_blockers"] == [
            "generated_delivery_surface_cannot_be_edit_source",
            "generated_delivery_surface_cannot_be_quality_authority",
            "generated_delivery_surface_cannot_be_dispatch_authority",
        ]


def test_delivery_package_layout_projection_separates_v2_legacy_and_unknown_surfaces(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_inventory")
    study_root = tmp_path / "studies" / "001-risk"
    v2_root = study_root / "manuscript" / "current_package"
    legacy_root = study_root / "paper" / "submission_minimal"
    v2_docx = _write(v2_root / "manuscript.docx")
    v2_audit = _write(v2_root / "audit" / "submission_manifest.json", "{}\n")
    v2_reproducibility = _write(v2_root / "reproducibility" / "source_signature.json", "{}\n")
    legacy_manifest = _write(legacy_root / "submission_manifest.json", "{}\n")
    legacy_pdf = _write(legacy_root / "paper.pdf", "%PDF\n")
    unknown_pdf = _write(study_root / "paper" / "build" / "paper.pdf", "%PDF\n")

    inventory = module.build_artifact_lifecycle_inventory(
        study_root=study_root,
        paths=(v2_docx, v2_audit, v2_reproducibility, legacy_manifest, legacy_pdf, unknown_pdf),
    )

    by_path = {Path(item["path"]): item for item in inventory["artifacts"]}
    assert inventory["summary"]["delivery_package_layout_status_counts"] == {
        "v2": 3,
        "legacy": 2,
        "unknown": 1,
    }
    assert by_path[v2_docx.resolve()]["delivery_package_layout"] == {
        "status": "v2",
        "package_root": str(v2_root.resolve()),
        "package_surface": "current_package",
        "section": "human_submission_files",
        "audit_root": str((v2_root / "audit").resolve()),
        "reproducibility_root": str((v2_root / "reproducibility").resolve()),
        "legacy_root_audit_files_present": False,
        "open_guidance": "open_root_submission_files",
        "audit_guidance": "inspect_audit_and_reproducibility_directories",
        "edit_source_allowed": False,
    }
    assert by_path[v2_audit.resolve()]["delivery_package_layout"]["section"] == "audit"
    assert by_path[v2_reproducibility.resolve()]["delivery_package_layout"]["section"] == "reproducibility"
    assert by_path[legacy_manifest.resolve()]["delivery_package_layout"]["status"] == "legacy"
    assert by_path[legacy_manifest.resolve()]["delivery_package_layout"]["section"] == "legacy_root_audit"
    assert by_path[legacy_pdf.resolve()]["delivery_package_layout"]["section"] == "human_submission_files"
    assert by_path[unknown_pdf.resolve()]["delivery_package_layout"] == {
        "status": "unknown",
        "package_root": str((study_root / "paper" / "build").resolve()),
        "package_surface": "generated_output",
        "section": "unknown_generated_output",
        "audit_root": None,
        "reproducibility_root": None,
        "legacy_root_audit_files_present": False,
        "open_guidance": "layout_unknown_inspect_file_directly",
        "audit_guidance": "audit_and_reproducibility_locations_unknown",
        "edit_source_allowed": False,
    }


def test_paper_artifact_resolver_exposes_projection_only_authority_for_submission_outputs(tmp_path: Path) -> None:
    paper_artifacts = importlib.import_module("med_autoscience.runtime_protocol.paper_artifacts")
    paper_bundle_manifest = tmp_path / "study" / "paper" / "paper_bundle_manifest.json"
    paper_bundle_manifest.parent.mkdir(parents=True, exist_ok=True)
    paper_bundle_manifest.write_text(json.dumps({"schema_version": 1}) + "\n", encoding="utf-8")
    submission_manifest = {
        "manuscript": {
            "docx_path": "paper/submission_minimal/manuscript.docx",
            "pdf_path": "paper/submission_minimal/paper.pdf",
        }
    }

    resolution = paper_artifacts.resolve_submission_minimal_artifact_authority(
        paper_bundle_manifest_path=paper_bundle_manifest,
        submission_minimal_manifest=submission_manifest,
    )

    assert resolution["status"] == "resolved"
    assert resolution["docx"]["role"] == "derived_projection"
    assert resolution["pdf"]["role"] == "derived_projection"
    assert resolution["docx"]["edit_source_allowed"] is False
    assert resolution["pdf"]["quality_authority_allowed"] is False
    assert resolution["docx"]["dispatch_authority_allowed"] is False
    assert resolution["pdf"]["dispatch_authority_allowed"] is False
    assert resolution["submission_minimal_dispatch_authority_allowed"] is False


def test_live_runtime_inventory_is_audit_only(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_inventory")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    runtime_log = _write(quest_root / ".ds" / "runs" / "run-live" / "stdout.jsonl")

    inventory = module.build_artifact_lifecycle_inventory(
        study_root=tmp_path / "studies" / "001-risk",
        quest_root=quest_root,
        paths=(runtime_log,),
        runtime_status={"status": "running", "active_run_id": "run-live"},
    )

    artifact = inventory["artifacts"][0]
    assert artifact["role"] == "runtime_ephemeral"
    assert artifact["lifecycle"] == "runtime_transient"
    assert artifact["cleanup_candidate_action"] == "audit-only"
    assert artifact["cleanup_blockers"] == ["live_runtime_active"]


def test_terminal_runtime_inventory_is_archive_compress_candidate(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_inventory")
    quest_root = tmp_path / "runtime" / "quests" / "001-risk"
    runtime_log = _write(quest_root / ".ds" / "runs" / "run-stopped" / "stdout.jsonl")

    inventory = module.build_artifact_lifecycle_inventory(
        study_root=tmp_path / "studies" / "001-risk",
        quest_root=quest_root,
        paths=(runtime_log,),
        runtime_status={"status": "stopped", "active_run_id": None},
    )

    artifact = inventory["artifacts"][0]
    assert artifact["role"] == "runtime_ephemeral"
    assert artifact["cleanup_candidate_action"] == "archive-compress"
    assert artifact["cleanup_blockers"] == []


def test_archive_cleanup_requires_restore_index_checksum_and_rehydrate_verification(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_inventory")
    archive_path = _write(tmp_path / "runtime" / "quests" / "001-risk" / ".ds" / "cold_archive" / "payload.tar.gz")

    missing = module.evaluate_archive_cleanup_readiness(
        archive_path=archive_path,
        restore_metadata={},
    )
    verified = module.evaluate_archive_cleanup_readiness(
        archive_path=archive_path,
        restore_metadata={
            "restore_index_path": "restore_index.json",
            "sha256": "abc123",
            "rehydrate_verification": {"status": "verified"},
        },
    )

    assert missing["candidate_action"] == "blocked"
    assert missing["physical_cleanup_allowed"] is False
    assert missing["blockers"] == [
        "missing_restore_index",
        "missing_checksum",
        "missing_rehydrate_verification",
    ]
    assert verified["candidate_action"] == "cleanup-expanded-copy"
    assert verified["physical_cleanup_allowed"] is True
    assert verified["blockers"] == []


def test_delivery_manifest_records_lifecycle_authority_sync(tmp_path: Path) -> None:
    delivery_sync = importlib.import_module("med_autoscience.controllers.study_delivery_sync")
    shared = importlib.import_module("tests.test_study_delivery_sync_cases.shared")
    paper_root, study_root = shared.make_delivery_workspace(tmp_path)

    manifest = delivery_sync.sync_study_delivery(
        paper_root=paper_root,
        stage="submission_minimal",
    )

    lifecycle = manifest["artifact_lifecycle"]
    assert lifecycle["surface_kind"] == "study_delivery_sync_lifecycle"
    assert lifecycle["authority_sync"]["status"] == "projection_only"
    assert lifecycle["authority_sync"]["direct_edit_allowed"] is False
    assert lifecycle["authority_sync"]["quality_authority_allowed"] is False
    assert lifecycle["lifecycle_roles"]["current_package"] == "derived_projection"
    assert lifecycle["lifecycle_roles"]["submission_minimal"] == "controller_authorized_package_source"
    assert lifecycle["delivery_package_roles"] == {
        "submission_minimal": "controller_authorized_package_source",
        "current_package": "human_facing_mirror",
    }


def test_v2_current_package_audit_manifest_is_projection_only_read_model(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.artifact_lifecycle_inventory")
    study_root = tmp_path / "studies" / "001-risk"
    audit_manifest = _write(
        study_root / "manuscript" / "current_package" / "audit" / "submission_manifest.json",
        "{}\n",
    )

    artifact = module.classify_artifact(path=audit_manifest, study_root=study_root)

    assert artifact["role"] == "derived_projection"
    assert artifact["lifecycle"] == "rebuildable_projection"
    assert artifact["projection_currentness"] == "projection_only"
    assert artifact["authority_allowed"] == {"edit": False, "quality": False, "dispatch": False}
    assert artifact["edit_source_allowed"] is False
    assert artifact["quality_authority_allowed"] is False
    assert artifact["dispatch_authority_allowed"] is False


def test_submission_surface_docx_inspector_is_read_only_for_generated_projection(tmp_path: Path) -> None:
    submission_minimal = importlib.import_module("med_autoscience.controllers.submission_minimal")
    docx_path = _write(tmp_path / "study" / "paper" / "submission_minimal" / "manuscript.docx", "not-a-zip\n")
    before_bytes = docx_path.read_bytes()
    before_mtime_ns = docx_path.stat().st_mtime_ns

    first = submission_minimal.inspect_submission_docx_surface(docx_path)
    second = submission_minimal.inspect_submission_docx_surface(docx_path)

    assert first == second
    assert first["exists"] is True
    assert first["unreadable"] is True
    assert docx_path.read_bytes() == before_bytes
    assert docx_path.stat().st_mtime_ns == before_mtime_ns


def test_delivery_inspector_reads_legacy_surface_without_materializing_v2_layout(tmp_path: Path) -> None:
    inspector = importlib.import_module("med_autoscience.controllers.delivery_inspector")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "repo"
    study_root = workspace_root / "studies" / "001-legacy-delivery"
    source_root = study_root / "paper" / "submission_minimal"
    human_root = study_root / "manuscript" / "current_package"
    profile_path = tmp_path / "profile.local.toml"
    _write(study_root / "study.yaml", "study_id: 001-legacy-delivery\n")
    _write(source_root / "manuscript.docx", "docx\n")
    _write(source_root / "paper.pdf", "%PDF-1.4\n")
    _write(source_root / "submission_manifest.json", '{"schema_version":1,"source_signature":"legacy-source"}\n')
    _write(human_root / "manuscript.docx", "docx\n")
    _write(human_root / "paper.pdf", "%PDF-1.4\n")
    _write(human_root / "submission_manifest.json", '{"schema_version":1,"source_signature":"legacy-mirror"}\n')
    profile_path.write_text(
        "\n".join(
            [
                'name = "legacy-delivery"',
                f'workspace_root = "{workspace_root}"',
                f'runtime_root = "{workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests"}"',
                f'studies_root = "{workspace_root / "studies"}"',
                f'portfolio_root = "{workspace_root / "portfolio"}"',
                f'med_deepscientist_runtime_root = "{workspace_root / "ops" / "med-deepscientist" / "runtime"}"',
                f'med_deepscientist_repo_root = "{workspace_root.parent / "med-deepscientist"}"',
                f'hermes_agent_repo_root = "{workspace_root.parent / "_external" / "hermes-agent"}"',
                'hermes_home_root = "~/.hermes"',
                'default_publication_profile = "general_medical_journal"',
                'default_citation_style = "AMA"',
                "enable_medical_overlay = true",
                'medical_overlay_scope = "workspace"',
                'medical_overlay_skills = ["scout", "idea", "decision", "write", "finalize"]',
                'medical_overlay_bootstrap_mode = "ensure_ready"',
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = inspector.inspect_study_delivery(
        profile=profiles.load_profile(profile_path),
        profile_ref=profile_path,
        study_id=study_root.name,
    )

    assert result["mutation_policy"] == {"read_only": True, "writes_package": False}
    assert result["freshness"]["verdict"] == "legacy"
    assert result["source_package"]["layout_status"] == "legacy"
    assert result["human_package"]["layout_status"] == "legacy"
    assert not (source_root / "audit").exists()
    assert not (human_root / "audit").exists()
