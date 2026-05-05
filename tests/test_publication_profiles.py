from __future__ import annotations

import importlib
from pathlib import Path


def test_jacs_publication_profile_is_explicitly_supported() -> None:
    module = importlib.import_module("med_autoscience.publication_profiles")

    assert module.is_supported_publication_profile("jacs") is True
    assert module.exporter_family_for_publication_profile("jacs") == "acs_publication"
    assert module.default_citation_style_for_publication_profile("jacs") == "ACS"
    assert module.publication_profile_supports_citation_style("jacs", "ACS") is True
    assert module.publication_profile_supports_citation_style("jacs", "AMA") is False


def test_jacs_submission_profile_config_uses_acs_package_surface() -> None:
    module = importlib.import_module("med_autoscience.controllers.submission_minimal_parts.shared_base")

    config = module.resolve_publication_profile_config(publication_profile="jacs", citation_style="auto")

    assert config.publication_profile == "jacs"
    assert config.citation_style == "ACS"
    assert config.output_dir_rel == Path("journal_submissions") / "jacs"
    assert config.csl_path.name == "american-chemical-society.csl"
    assert config.csl_path.exists()
