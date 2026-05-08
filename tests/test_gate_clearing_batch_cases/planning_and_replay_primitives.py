from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_submission_minimal_fingerprint_payload_ignores_materialized_submission_source_from_compile_report(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    submission_minimal_tests = importlib.import_module("tests.test_submission_minimal")
    paper_root = submission_minimal_tests.make_materialized_submission_source_workspace(tmp_path)
    profile = make_profile(tmp_path)

    payload = module._submission_minimal_fingerprint_payload(
        paper_root=paper_root,
        gate_report={
            "status": "blocked",
            "blockers": ["stale_submission_minimal_authority"],
            "current_required_action": "complete_bundle_stage",
            "medical_publication_surface_status": "clear",
            "study_delivery_status": "current",
        },
        profile=profile,
    )

    assert payload["compiled_markdown"]["path"] == str((paper_root / "draft.md").resolve())

def test_execute_repair_units_treats_all_skipped_dependents_as_terminal_state(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    paper_root = tmp_path / "paper"
    paper_root.mkdir(parents=True)

    def _raise_failure() -> dict[str, Any]:
        raise RuntimeError("simulated upstream failure")

    repair_units = [
        module.GateClearingRepairUnit(
            unit_id="upstream_failure",
            label="upstream failure",
            parallel_safe=True,
            run=_raise_failure,
        ),
        module.GateClearingRepairUnit(
            unit_id="dependent_parallel",
            label="dependent parallel",
            parallel_safe=True,
            run=lambda: {"status": "ok"},
            depends_on=("upstream_failure",),
        ),
        module.GateClearingRepairUnit(
            unit_id="dependent_sequential",
            label="dependent sequential",
            parallel_safe=False,
            run=lambda: {"status": "ok"},
            depends_on=("upstream_failure", "dependent_parallel"),
        ),
    ]

    unit_results, unit_fingerprints, execution_summary = module._execute_repair_units(
        repair_units=repair_units,
        latest_batch={},
        paper_root=paper_root,
        gate_report={},
        profile=profile,
    )

    assert [item["status"] for item in unit_results] == [
        "failed",
        "skipped_failed_dependency",
        "skipped_failed_dependency",
    ]
    assert unit_results[1]["failed_dependencies"] == ["upstream_failure"]
    assert unit_results[2]["failed_dependencies"] == ["upstream_failure", "dependent_parallel"]
    assert unit_fingerprints == {}
    assert execution_summary == {
        "parallel_wave_count": 1,
        "parallel_unit_count": 1,
        "sequential_unit_count": 0,
        "skipped_dependency_unit_count": 2,
    }

def test_parse_json_object_from_cli_stdout_ignores_launcher_preamble() -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")

    payload = module._parse_json_object_from_cli_stdout(
        "\n".join(
            [
                "DeepScientist detected a runtime change and is rebuilding the local uv-managed environment.",
                "[1/2] Preparing uv-managed Python runtime",
                "{",
                '  "ok": true,',
                '  "status": "updated",',
                '  "repaired_files": ["paper/claim_evidence_map.json"]',
                "}",
            ]
        )
    )

    assert payload == {
        "ok": True,
        "status": "updated",
        "repaired_files": ["paper/claim_evidence_map.json"],
    }
