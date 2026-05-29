from __future__ import annotations

from .shared import *


def test_describe_submission_minimal_authority_prefers_v2_manifest_over_stale_legacy_root(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )
    submission_root = paper_root / "submission_minimal"
    legacy_manifest_path = submission_root / "submission_manifest.json"
    dump_json(
        legacy_manifest_path,
        {
            "schema_version": 1,
            "source_signature": "stale-legacy-root-signature",
            "source_contract": {"source_signature": "stale-legacy-root-signature"},
        },
    )

    authority = module.describe_submission_minimal_authority(paper_root=paper_root)

    assert authority["status"] == "current"
    assert authority["stale_reason"] is None
    assert authority["submission_manifest_path"] == str(submission_root / "audit" / "submission_manifest.json")
    assert authority["recorded_source_signature"] != "stale-legacy-root-signature"


def test_describe_submission_minimal_authority_reads_legacy_manifest_when_v2_manifest_is_absent(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )
    submission_root = paper_root / "submission_minimal"
    legacy_manifest_path = submission_root / "submission_manifest.json"
    (submission_root / "audit" / "submission_manifest.json").unlink()
    dump_json(legacy_manifest_path, manifest)

    authority = module.describe_submission_minimal_authority(paper_root=paper_root)

    assert authority["status"] == "current"
    assert authority["stale_reason"] is None
    assert authority["submission_manifest_path"] == str(legacy_manifest_path)
    assert authority["recorded_source_signature"] == manifest["source_signature"]


def test_submission_minimal_v2_layout_records_source_contract_in_reproducibility_docs(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    source_signature_doc = json.loads(
        (submission_root / "reproducibility" / "source_signature.json").read_text(encoding="utf-8")
    )
    source_paths_doc = json.loads(
        (submission_root / "reproducibility" / "source_relative_paths.json").read_text(encoding="utf-8")
    )

    assert source_signature_doc["layout_version"] == "submission-package.v2"
    assert source_signature_doc["package_role"] == "controller_authorized_package_source"
    assert source_signature_doc["source_signature"] == manifest["source_signature"]
    assert source_signature_doc["source_contract"]["source_signature"] == manifest["source_signature"]
    assert source_paths_doc["layout_version"] == "submission-package.v2"
    assert source_paths_doc["package_role"] == "controller_authorized_package_source"
    assert "paper/build/review_manuscript.md" in source_paths_doc["source_relative_paths"]
    assert "paper/submission_minimal/manuscript.docx" not in source_paths_doc["source_relative_paths"]


def test_submission_minimal_v2_layout_writes_reproducibility_lineage_bundle(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal")
    paper_root = make_paper_workspace(tmp_path)

    manifest = module.create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    submission_root = paper_root / "submission_minimal"
    manifest_payload = json.loads(
        (submission_root / "audit" / "submission_manifest.json").read_text(encoding="utf-8")
    )
    source_signature_doc = json.loads(
        (submission_root / "reproducibility" / "source_signature.json").read_text(encoding="utf-8")
    )
    analysis_manifest = json.loads(
        (submission_root / "reproducibility" / "analysis_manifest.json").read_text(encoding="utf-8")
    )
    software_environment = json.loads(
        (submission_root / "reproducibility" / "software_environment.json").read_text(encoding="utf-8")
    )
    lineage_graph = json.loads(
        (submission_root / "reproducibility" / "artifact_lineage_graph.json").read_text(encoding="utf-8")
    )

    assert manifest_payload["delivery_layout"]["reproducibility_paths"]["software_environment"] == (
        "paper/submission_minimal/reproducibility/software_environment.json"
    )
    assert manifest_payload["delivery_layout"]["reproducibility_paths"]["artifact_lineage_graph"] == (
        "paper/submission_minimal/reproducibility/artifact_lineage_graph.json"
    )
    assert source_signature_doc["source_signature_sha256"] == manifest["source_signature"]
    assert source_signature_doc["artifact_lineage_graph_ref"] == (
        "reproducibility/artifact_lineage_graph.json"
    )
    assert analysis_manifest["analysis_results"] == [
        {
            "result_id": "analysis_outputs",
            "source_ref": "paper/build/compile_report.json",
            "sha256": next(
                item["sha256"]
                for item in manifest["source_contract"]["source_files"]
                if item["path"] == "paper/build/compile_report.json"
            ),
        }
    ]
    assert analysis_manifest["software_environment_ref"] == "reproducibility/software_environment.json"
    assert software_environment["environment_ref_status"] == "repo_runtime"
    assert software_environment["package_role"] == "controller_authorized_package_source"
    assert lineage_graph["lineage_chain"] == [
        "canonical_source",
        "analysis_result",
        "evidence_ledger",
        "claim_map",
        "manuscript_table_figure",
        "submission_package",
    ]
    assert {node["node_id"]: node["authority"] for node in lineage_graph["nodes"]} == {
        "canonical_source": "canonical_source_authority",
        "analysis_result": "analysis_output_projection",
        "evidence_ledger": "paper_evidence_authority",
        "claim_map": "claim_evidence_projection",
        "manuscript_table_figure": "generated_delivery_projection",
        "submission_package": "controller_authorized_delivery_projection",
    }
    assert [(edge["from"], edge["to"]) for edge in lineage_graph["edges"]] == [
        ("canonical_source", "analysis_result"),
        ("analysis_result", "evidence_ledger"),
        ("evidence_ledger", "claim_map"),
        ("claim_map", "manuscript_table_figure"),
        ("manuscript_table_figure", "submission_package"),
    ]
    assert lineage_graph["derived_projection_boundaries"] == {
        "edit_source": False,
        "quality_authority": False,
        "dispatch_authority": False,
    }
    assert lineage_graph["source_signature_sha256"] == manifest["source_signature"]
