from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_gate_clearing_batch_reexports_natural_boundary_modules(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    execution = importlib.import_module("med_autoscience.controllers.gate_clearing_batch_execution")
    repair_fingerprints = importlib.import_module(
        "med_autoscience.controllers.gate_clearing_batch_repair_fingerprints"
    )

    repair_unit = module.GateClearingRepairUnit(
        unit_id="materialize_display_surface",
        label="materialize display surface",
        parallel_safe=True,
        run=lambda: {"status": "materialized"},
    )

    assert module.GateClearingRepairUnit is execution.GateClearingRepairUnit
    assert module._existing_dependency_ids([repair_unit], "materialize_display_surface", "missing") == (
        "materialize_display_surface",
    )
    assert execution.existing_dependency_ids([repair_unit], "materialize_display_surface", "missing") == (
        "materialize_display_surface",
    )
    assert module._unit_status_blocks_dependents("failed") is True
    assert execution.unit_status_blocks_dependents("failed") is True
    assert module._unit_status_is_success("updated") is True
    assert execution.unit_status_is_success("updated") is True

    paper_root = tmp_path / "paper"
    paper_root.mkdir()
    gate_report = {
        "status": "blocked",
        "blockers": ["medical_publication_surface_blocked"],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
    }

    assert module._repair_unit_fingerprint(
        unit_id="materialize_display_surface",
        paper_root=paper_root,
        gate_report=gate_report,
    ) == repair_fingerprints.repair_unit_fingerprint(
        unit_id="materialize_display_surface",
        paper_root=paper_root,
        gate_report=gate_report,
        profile=None,
        submission_minimal_controller=module.submission_minimal,
        path_fingerprint=module._path_fingerprint,
        path_fingerprints=module._path_fingerprints,
        globbed_path_fingerprints=module._globbed_path_fingerprints,
    )
