from __future__ import annotations

import importlib
from pathlib import Path

import pytest


def _record(*, record_id: str, title: str, doi: str, pmid: str | None = None) -> dict[str, object]:
    return {
        "record_id": record_id,
        "title": title,
        "authors": ["A. Author"],
        "year": 2024,
        "journal": "BMC Medicine",
        "doi": doi,
        "pmid": pmid,
        "pmcid": None,
        "arxiv_id": None,
        "abstract": "Structured abstract",
        "full_text_availability": "metadata_only",
        "source_priority": 3,
        "citation_payload": {"doi": doi},
        "local_asset_paths": [],
        "relevance_role": "anchor_paper",
        "claim_support_scope": ["paper_framing"],
    }


def test_workspace_literature_init_returns_opl_owner_refs_without_materializing_files(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_literature")
    workspace_root = tmp_path / "workspace"

    result = module.init_workspace_literature(workspace_root=workspace_root)

    assert result["status"] == "opl_source_intake_required"
    assert result["created_files"] == []
    assert result["workspace_literature_root"] is None
    assert result["registry_path"] is None
    assert result["opl_owner_refs"]["scientific_connector"].endswith(
        "opl-connect-scientific.ts"
    )
    assert not workspace_root.exists()


def test_workspace_literature_sync_emits_deduped_medical_refs_for_opl_transport(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_literature")

    result = module.sync_workspace_literature(
        workspace_root=tmp_path / "workspace",
        records=[
            _record(record_id="seed-anchor", title="Prediction model paper", doi="10.1000/example"),
            _record(record_id="dup-anchor", title="Prediction model paper", doi="10.1000/example"),
        ],
    )

    assert result["status"] == "opl_source_intake_required"
    assert result["record_count"] == 1
    assert result["records"][0]["record_id"] == "doi:10.1000/example"
    assert result["source_refs"][0]["ref_kind"] == "medical_literature_ref"
    assert result["authority_boundary"]["mas_materializes_workspace_bibtex"] is False


def test_workspace_literature_sync_rejects_conflicting_domain_records(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.workspace_literature")

    with pytest.raises(ValueError, match="conflicting canonical literature record"):
        module.sync_workspace_literature(
            workspace_root=tmp_path / "workspace",
            records=[
                _record(record_id="seed-anchor", title="Prediction model paper", doi="10.1000/example"),
                _record(record_id="dup-anchor", title="Different paper title", doi="10.1000/example"),
            ],
        )
