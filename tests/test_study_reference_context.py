from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_build_study_reference_context_writes_artifact_and_emits_opl_source_intake(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_reference_context")
    workspace_contracts = importlib.import_module("med_autoscience.workspace_contracts")
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    workspace_root = tmp_path / "workspace"

    monkeypatch.setattr(
        module.startup_literature,
        "resolve_startup_literature",
        lambda *, startup_contract, provider_receipts=(): {
            "status": "resolved",
            "provider_receipt_refs": ["opl://connect/references/verify/startup"],
            "provider_resolution_requests": [],
            "records": [{
                "record_id": "pmid:12345",
                "title": "Prediction model paper",
                "authors": ["A. Author"],
                "year": 2024,
                "journal": "BMC Medicine",
                "doi": "10.1000/example",
                "pmid": "12345",
                "pmcid": None,
                "arxiv_id": None,
                "abstract": "Structured abstract",
                "full_text_availability": "abstract_only",
                "source_priority": 2,
                "citation_payload": {"journal": "BMC Medicine"},
                "local_asset_paths": [],
                "relevance_role": "anchor_paper",
                "claim_support_scope": ["paper_framing"],
            }],
        },
    )

    context = module.build_study_reference_context(
        study_root=study_root,
        workspace_root=workspace_root,
        startup_contract={
            "reference_papers": [
                {
                    "id": "li2023-bmj",
                    "title": "Gray-zone triage workflow",
                    "doi": "10.1000/example-2",
                    "role": "closest_competitor",
                }
            ]
        },
    )

    artifact_path = study_root / "artifacts" / "reference_context" / "latest.json"
    assert artifact_path.is_file()
    assert context["artifact_path"] == str(artifact_path)
    assert context["workspace_registry_path"] is None
    assert context["workspace_source_intake_request"]["status"] == "opl_source_intake_required"
    assert context["workspace_source_intake_request"]["record_count"] == 2
    assert context["record_count"] == 2
    assert context["startup_provider_resolution"] == {
        "status": "resolved",
        "provider_receipt_refs": ["opl://connect/references/verify/startup"],
        "provider_resolution_requests": [],
    }
    assert context["mandatory_anchor_record_ids"] == ["pmid:12345"]
    assert context["selected_record_ids"] == ["pmid:12345", "doi:10.1000/example-2"]
    assert context["selections"] == [
        {
            "record_id": "pmid:12345",
            "study_role": "framing_anchor",
            "source_layer": "startup_contract",
        },
        {
            "record_id": "doi:10.1000/example-2",
            "study_role": "claim_support",
            "source_layer": "reference_papers",
        },
    ]
    assert context["records"][0]["relevance_role"] == "framing_anchor"
    assert context["records"][1]["relevance_role"] == "claim_support"

    persisted = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert persisted["selected_record_ids"] == ["pmid:12345", "doi:10.1000/example-2"]

    status = workspace_contracts.workspace_literature_status(workspace_root=workspace_root)
    assert status["status"] == "opl_managed"
    assert status["record_count"] == 0
