from __future__ import annotations

import pytest

from med_autoscience.controllers.architecture_owner_boundary import (
    build_architecture_owner_boundary_report,
    validate_architecture_owner_boundary_report,
)


pytestmark = pytest.mark.meta


def test_architecture_owner_boundary_keeps_opl_authority_out_of_mas() -> None:
    report = build_architecture_owner_boundary_report()
    layers = {item["layer_id"]: item for item in report["owner_layers"]}

    assert validate_architecture_owner_boundary_report(report)["ok"] is True
    assert layers["opl_progress_spine"]["owner"] == "one-person-lab"
    assert layers["mas_runtime_diagnostic_refs"]["authority_surfaces"] == []
    assert layers["mas_runtime_diagnostic_refs"]["owned_progress_spine_surfaces"] == []

    layers["mas_runtime_diagnostic_refs"]["authority_surfaces"] = ["runtime_health"]
    issue_codes = {
        item["code"]
        for item in validate_architecture_owner_boundary_report(report)["issues"]
    }
    assert {
        "mas_claims_opl_runtime_lifecycle_authority",
        "mas_claims_opl_progress_spine_authority",
    } <= issue_codes
