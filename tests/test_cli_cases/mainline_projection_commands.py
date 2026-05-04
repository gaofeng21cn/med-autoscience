from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_mainline_status_cli_projects_unified_enhancement_program(capsys) -> None:
    cli = importlib.import_module("med_autoscience.cli")

    exit_code = cli.main(["doctor", "mainline-status", "--format", "json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    program = payload["unified_enhancement_program"]

    assert exit_code == 0
    assert program["projection_only"] is True
    assert "does not become quality, submission, delivery, runtime, or controller authority" in (
        program["authority_boundary"]
    )
    assert len(program["lanes"]) == 5
    assert len(program["recommendation_rollup"]) == 15
    assert [item["boundary_id"] for item in program["module_boundary_audit"]["boundaries"]] == [
        "study_truth",
        "runtime_truth",
        "quality_truth",
        "delivery_truth",
        "maintainability_truth",
    ]
