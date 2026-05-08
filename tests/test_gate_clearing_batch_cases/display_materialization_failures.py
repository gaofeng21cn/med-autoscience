from __future__ import annotations

import os

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_display_materialization_missing_registry_records_blocking_artifact_ref(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-dm-china-us-mortality-attribution", quest_id="quest-002")
    paper_root = study_root / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    missing_registry = paper_root / "display_registry.json"
    repair_units = [
        module.GateClearingRepairUnit(
            unit_id="materialize_display_surface",
            label="Refresh display catalogs and generated paper-facing exports",
            parallel_safe=True,
            run=lambda: (_ for _ in ()).throw(FileNotFoundError(2, "No such file or directory", str(missing_registry))),
        )
    ]

    unit_results, _, _ = module._execute_repair_units(
        repair_units=repair_units,
        latest_batch={},
        paper_root=paper_root,
        gate_report={"status": "blocked"},
        profile=profile,
    )

    result = unit_results[0]
    assert result["status"] == "failed"
    assert result["terminal_state"] == "gate_needs_specificity"
    assert result["blocking_artifact_refs"] == [
        {
            "blocker": "display_surface_materialization_failed",
            "artifact_path": str(missing_registry.resolve()),
            "artifact_role": "display_registry",
            "failure_reason": f"[Errno 2] No such file or directory: '{missing_registry}'",
            "terminal_state": "gate_needs_specificity",
        }
    ]


def test_display_materialization_matching_input_failure_is_reused_as_blocked(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-dm-china-us-mortality-attribution", quest_id="quest-002")
    paper_root = study_root / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    cohort_flow = paper_root / "display_registry.json"
    _write_json(cohort_flow, {"steps": []})
    gate_report = {
        "status": "blocked",
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": ["cohort_flow_missing_steps"],
    }
    matching_fingerprint = module._repair_unit_fingerprint(
        unit_id="materialize_display_surface",
        paper_root=paper_root,
        gate_report=gate_report,
        profile=profile,
    )
    previous_refs = [
        {
            "blocker": "display_surface_materialization_failed",
            "artifact_path": str(cohort_flow.resolve()),
            "artifact_role": "display_input_payload",
            "failure_reason": "cohort_flow.json must contain a non-empty steps list",
            "terminal_state": "gate_needs_specificity",
        }
    ]
    latest_batch = {
        "unit_results": [
            {
                "unit_id": "materialize_display_surface",
                "status": "failed",
                "error": "cohort_flow.json must contain a non-empty steps list",
                "blocking_artifact_refs": previous_refs,
                "terminal_state": "gate_needs_specificity",
                "fingerprint": matching_fingerprint,
            }
        ],
        "unit_fingerprints": {
            "materialize_display_surface": matching_fingerprint,
        },
    }
    run_count = 0

    def rerun_materializer() -> dict[str, Any]:
        nonlocal run_count
        run_count += 1
        return {"status": "materialized"}

    repair_units = [
        module.GateClearingRepairUnit(
            unit_id="materialize_display_surface",
            label="Refresh display catalogs and generated paper-facing exports",
            parallel_safe=True,
            run=rerun_materializer,
        )
    ]

    unit_results, unit_fingerprints, _ = module._execute_repair_units(
        repair_units=repair_units,
        latest_batch=latest_batch,
        paper_root=paper_root,
        gate_report=gate_report,
        profile=profile,
    )

    assert run_count == 0
    result = unit_results[0]
    assert result["status"] == "blocked_matching_failed_unit_fingerprint"
    assert result["previous_status"] == "failed"
    assert result["previous_failure_reused"] is True
    assert result["blocking_artifact_refs"] == previous_refs
    assert result["terminal_state"] == "gate_needs_specificity"
    assert result["fingerprint"] == matching_fingerprint
    assert unit_fingerprints == {"materialize_display_surface": matching_fingerprint}


def test_display_materialization_fingerprint_uses_json_content_not_mtime(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-dm-china-us-mortality-attribution", quest_id="quest-002")
    paper_root = study_root / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    gate_report = {
        "status": "blocked",
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": ["cohort_flow_missing_steps"],
    }
    cohort_flow = paper_root / "display_registry.json"
    payload = {"schema_version": 1, "steps": []}
    _write_json(cohort_flow, payload)
    first = module._repair_unit_fingerprint(
        unit_id="materialize_display_surface",
        paper_root=paper_root,
        gate_report=gate_report,
        profile=profile,
    )
    stat = cohort_flow.stat()
    os.utime(cohort_flow, ns=(stat.st_atime_ns, stat.st_mtime_ns + 10_000_000_000))
    second = module._repair_unit_fingerprint(
        unit_id="materialize_display_surface",
        paper_root=paper_root,
        gate_report=gate_report,
        profile=profile,
    )

    assert second == first


def test_gate_clearing_batch_record_binds_source_work_unit_fingerprint(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.gate_clearing_batch")
    publication_work_units = importlib.import_module("med_autoscience.controllers.publication_work_units")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "002-dm-china-us-mortality-attribution", quest_id="quest-002")
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    paper_root = quest_root / ".ds" / "worktrees" / "paper-run-002" / "paper"
    paper_root.mkdir(parents=True, exist_ok=True)
    gate_report = {
        "status": "blocked",
        "blockers": ["medical_publication_surface_blocked", "claim_evidence_consistency_failed"],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_named_blockers": ["claim_evidence_consistency_failed"],
        "study_delivery_status": "current",
        "gate_fingerprint": "publication-gate::dm002",
        "submission_minimal_evaluated_source_signature": "source::same",
        "submission_minimal_authority_source_signature": "source::same",
        "blocking_artifact_refs": [
            {
                "blocker": "claim_evidence_consistency_failed",
                "claim_id": "primary_dm_mortality_attribution_claim",
                "source_path": str(study_root / "artifacts" / "results" / "main_result.json"),
            }
        ],
    }
    work_unit_fingerprint = publication_work_units.derive_publication_work_units(gate_report)["fingerprint"]
    publication_eval_payload = _write_blocked_publication_eval(study_root, quest_id="quest-002")
    publication_eval_payload["recommended_actions"][0]["work_unit_fingerprint"] = work_unit_fingerprint
    publication_eval_payload["recommended_actions"][0]["next_work_unit"] = {
        "unit_id": "analysis_claim_evidence_repair",
        "lane": "analysis-campaign",
        "summary": "Repair claim-evidence and display traceability blockers.",
    }
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", publication_eval_payload)

    monkeypatch.setattr(
        module.publication_gate,
        "build_gate_state",
        lambda _quest_root: type("GateState", (), {"paper_root": paper_root})(),
    )
    monkeypatch.setattr(module.publication_gate, "build_gate_report", lambda _state: dict(gate_report))
    monkeypatch.setattr(module, "_eligible_mapping_payload", lambda **_: (None, {}))
    monkeypatch.setattr(module, "_repair_paper_live_paths", lambda **_: {"status": "updated", "repaired_files": []})
    monkeypatch.setattr(module, "_materialize_display_surface", lambda **_: {"status": "materialized"})
    monkeypatch.setattr(
        module.publication_gate,
        "run_controller",
        lambda **_: {"status": "blocked", "allow_write": False, "blockers": ["claim_evidence_consistency_failed"]},
    )

    result = module.run_gate_clearing_batch(
        profile=profile,
        study_id="002-dm-china-us-mortality-attribution",
        study_root=study_root,
        quest_id="quest-002",
        source="test-source",
    )

    assert result["status"] == "executed"
    saved = json.loads(Path(result["record_path"]).read_text(encoding="utf-8"))
    assert saved["source_eval_id"] == publication_eval_payload["eval_id"]
    assert saved["source_work_unit_fingerprint"] == work_unit_fingerprint
    assert saved["work_unit_fingerprint"] == work_unit_fingerprint
