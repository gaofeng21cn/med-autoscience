from __future__ import annotations

from med_autoscience.dev_preflight_contract import classify_changed_files


def test_hosted_ordinary_path_changes_are_standard_agent_pack_surface() -> None:
    result = classify_changed_files(
        (
            "contracts/hosted_ordinary_path_consumption.json",
            "src/med_autoscience/hosted_ordinary_path_consumption.py",
            "tests/test_hosted_ordinary_path_consumption.py",
            "tests/test_agent_tool_arsenal_hosted_consumption_mcp.py",
            "tests/test_hosted_ordinary_path_preflight_contract.py",
        )
    )

    assert result.matched_categories == ("standard_agent_pack_surface",)
    assert result.unclassified_changes == ()
