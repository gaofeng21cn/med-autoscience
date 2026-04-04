from __future__ import annotations

import importlib
import json
from pathlib import Path


def test_load_publication_style_profile_requires_palette_and_semantic_roles(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.publication_display_contract")
    path = tmp_path / "publication_style_profile.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "style_profile_id": "paper_neutral_clinical_v1",
                "palette": {"primary": "#5F766B"},
            }
        ),
        encoding="utf-8",
    )

    try:
        module.load_publication_style_profile(path)
    except ValueError as exc:
        assert "semantic_roles" in str(exc)
    else:
        raise AssertionError("expected load_publication_style_profile to reject missing semantic_roles")


def test_load_display_overrides_requires_displays_list(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.publication_display_contract")
    path = tmp_path / "display_overrides.json"
    path.write_text(json.dumps({"schema_version": 1, "displays": {}}), encoding="utf-8")

    try:
        module.load_display_overrides(path)
    except ValueError as exc:
        assert "displays" in str(exc)
    else:
        raise AssertionError("expected load_display_overrides to reject non-list displays")


def test_load_display_overrides_returns_keyed_mapping(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.publication_display_contract")
    path = tmp_path / "display_overrides.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "displays": [
                    {
                        "display_id": "decision_curve",
                        "template_id": "time_to_event_decision_curve",
                        "layout_override": {"legend_position": "lower_center"},
                        "readability_override": {"focus_window": {"panel_id": "A"}},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    loaded = module.load_display_overrides(path)
    override = loaded[("decision_curve", "time_to_event_decision_curve")]
    assert override.display_id == "decision_curve"
    assert override.template_id == "time_to_event_decision_curve"


def test_load_publication_style_profile_rejects_non_string_values_in_maps(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.publication_display_contract")
    path = tmp_path / "publication_style_profile.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "style_profile_id": "paper_neutral_clinical_v1",
                "palette": {"primary": None, "secondary": "#B9AD9C", "neutral": "#7B8794"},
                "semantic_roles": {"model_curve": "primary"},
            }
        ),
        encoding="utf-8",
    )

    try:
        module.load_publication_style_profile(path)
    except ValueError as exc:
        assert "non-empty strings" in str(exc)
    else:
        raise AssertionError("expected non-string palette values to be rejected")


def test_load_publication_style_profile_rejects_bool_numeric_values(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.publication_display_contract")
    path = tmp_path / "publication_style_profile.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "style_profile_id": "paper_neutral_clinical_v1",
                "palette": {"primary": "#5F766B", "secondary": "#B9AD9C", "neutral": "#7B8794"},
                "semantic_roles": {"model_curve": "primary"},
                "typography": {"title_size": True},
            }
        ),
        encoding="utf-8",
    )

    try:
        module.load_publication_style_profile(path)
    except ValueError as exc:
        assert "must be numeric" in str(exc)
    else:
        raise AssertionError("expected bool numeric values to be rejected")


def test_load_publication_style_profile_rejects_invalid_schema_version(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.publication_display_contract")
    path = tmp_path / "publication_style_profile.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": True,
                "style_profile_id": "paper_neutral_clinical_v1",
                "palette": {"primary": "#5F766B", "secondary": "#B9AD9C", "neutral": "#7B8794"},
                "semantic_roles": {"model_curve": "primary"},
            }
        ),
        encoding="utf-8",
    )

    try:
        module.load_publication_style_profile(path)
    except ValueError as exc:
        assert "schema_version" in str(exc)
    else:
        raise AssertionError("expected invalid schema_version to be rejected")


def test_load_display_overrides_rejects_duplicate_override(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.publication_display_contract")
    path = tmp_path / "display_overrides.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "displays": [
                    {"display_id": "decision_curve", "template_id": "time_to_event_decision_curve"},
                    {"display_id": "decision_curve", "template_id": "time_to_event_decision_curve"},
                ],
            }
        ),
        encoding="utf-8",
    )

    try:
        module.load_display_overrides(path)
    except ValueError as exc:
        assert "duplicate override" in str(exc)
    else:
        raise AssertionError("expected duplicate overrides to be rejected")


def test_load_display_overrides_rejects_invalid_schema_version(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.publication_display_contract")
    path = tmp_path / "display_overrides.json"
    path.write_text(json.dumps({"schema_version": True, "displays": []}), encoding="utf-8")

    try:
        module.load_display_overrides(path)
    except ValueError as exc:
        assert "schema_version" in str(exc)
    else:
        raise AssertionError("expected invalid display_overrides schema_version to be rejected")


def test_load_publication_style_profile_rejects_non_string_style_profile_id(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.publication_display_contract")
    path = tmp_path / "publication_style_profile.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "style_profile_id": 123,
                "palette": {"primary": "#5F766B", "secondary": "#B9AD9C", "neutral": "#7B8794"},
                "semantic_roles": {"model_curve": "primary"},
            }
        ),
        encoding="utf-8",
    )

    try:
        module.load_publication_style_profile(path)
    except ValueError as exc:
        assert "style_profile_id" in str(exc)
    else:
        raise AssertionError("expected non-string style_profile_id to be rejected")


def test_load_display_overrides_rejects_non_string_identity_fields(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.publication_display_contract")
    path = tmp_path / "display_overrides.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "displays": [
                    {
                        "display_id": True,
                        "template_id": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    try:
        module.load_display_overrides(path)
    except ValueError as exc:
        assert "display_id" in str(exc) or "template_id" in str(exc)
    else:
        raise AssertionError("expected non-string display override identity fields to be rejected")
