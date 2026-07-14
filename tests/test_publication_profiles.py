from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


def test_jacs_publication_profile_is_explicitly_supported() -> None:
    module = importlib.import_module("med_autoscience.publication_profiles")

    assert module.is_supported_publication_profile("jacs") is True
    assert module.exporter_family_for_publication_profile("jacs") == "acs_publication"
    assert module.default_citation_style_for_publication_profile("jacs") == "ACS"
    assert module.publication_profile_supports_citation_style("jacs", "ACS") is True
    assert module.publication_profile_supports_citation_style("jacs", "AMA") is False


def test_jacs_submission_profile_config_uses_acs_package_surface() -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal.profile_config")

    config = module.resolve_publication_profile_config(publication_profile="jacs", citation_style="auto")

    assert config.publication_profile == "jacs"
    assert config.citation_style == "ACS"
    assert config.output_dir_rel == Path("journal_submissions") / "jacs"
    assert config.csl_path.name == "american-chemical-society.csl"
    assert config.csl_path.exists()


def test_frontiers_profile_consumes_host_provisioned_exact_template_paths(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal.profile_config")
    manuscript = tmp_path / "Frontiers_Template.docx"
    supplementary = tmp_path / "Supplementary_Material.docx"
    csl = tmp_path / "frontiers.csl"
    for path in (manuscript, supplementary, csl):
        path.write_bytes(b"exact package resource")

    config = module.resolve_publication_profile_config(
        publication_profile="frontiers_family_harvard",
        citation_style="auto",
        provisioned_resources={
            module.FRONTIERS_TEMPLATE_RESOURCE_ID: manuscript,
            module.FRONTIERS_SUPPLEMENTARY_TEMPLATE_RESOURCE_ID: supplementary,
            module.FRONTIERS_CSL_RESOURCE_ID: csl,
        },
    )

    assert config.reference_doc_path == manuscript.resolve()
    assert config.supplementary_reference_doc_path == supplementary.resolve()
    assert config.csl_path == csl.resolve()


def test_frontiers_profile_requests_pack_resource_without_network_fallback(monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal.profile_config")
    for env_name in (
        module.FRONTIERS_TEMPLATE_ENV,
        module.FRONTIERS_SUPPLEMENTARY_TEMPLATE_ENV,
        module.FRONTIERS_CSL_ENV,
    ):
        monkeypatch.delenv(env_name, raising=False)

    with pytest.raises(module.MissingProvisionedSubmissionResource) as captured:
        module.resolve_publication_profile_config(
            publication_profile="frontiers_family_harvard",
            citation_style="auto",
        )

    assert captured.value.resolution == {
        "status": "request_only",
        "action_id": "opl_pack_provision_submission_resource",
        "resource_id": module.FRONTIERS_TEMPLATE_RESOURCE_ID,
        "path_env": module.FRONTIERS_TEMPLATE_ENV,
        "requires_existing_exact_path": True,
        "network_fallback_allowed": False,
    }


def test_submission_resource_contract_matches_runtime_requirements() -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal.profile_config")
    repo_root = Path(__file__).resolve().parents[1]
    contract_path = repo_root / "contracts" / "submission-resource-requirements.json"
    descriptor = json.loads((repo_root / "contracts" / "domain_descriptor.json").read_text(encoding="utf-8"))
    pack_input = json.loads((repo_root / "contracts" / "pack_compiler_input.json").read_text(encoding="utf-8"))

    assert json.loads(contract_path.read_text(encoding="utf-8")) == module.submission_resource_requirements()
    assert descriptor["standard_contract_refs"]["submission_resource_requirements"] == (
        "contracts/submission-resource-requirements.json"
    )
    assert pack_input["source_refs"]["submission_resource_requirements"] == (
        "contracts/submission-resource-requirements.json"
    )
