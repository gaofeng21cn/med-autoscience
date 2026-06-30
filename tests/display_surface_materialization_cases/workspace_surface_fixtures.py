from __future__ import annotations

import json

from med_autoscience import display_registry

from . import registry_id_helpers as _registry_id_helpers
from . import shared_base as _shared_base
from .current_evidence_payload_fixtures import (
    _current_evidence_input_envelopes,
)
from .registry_builders import _build_workspace_registry_displays, _workspace_template_bindings


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared_base)
_module_reexport(_registry_id_helpers)


def _write_prepared_dependency_environment(paper_root: Path) -> None:
    build_root = paper_root / "build"
    build_root.mkdir(parents=True, exist_ok=True)
    (build_root / "dependency_environment_lock.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "lock_id": "test-display-env-lock",
                "lock_sha256": "sha256:test-display-env-lock",
                "source_requirement_refs": [
                    "external/display-packs/medical-display-core/renderer_dependency_profile.json"
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (build_root / "dependency_run_context.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "run_context_id": "test-display-env-run-context",
                "execution_fingerprint": "sha256:test-display-env-run-context",
                "argv_prefix": [],
                "env_vars": {"MAS_TEST_DEPENDENCY_ENV": "prepared"},
                "binary_paths": {},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (build_root / "dependency_environment_receipt.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "status": "prepared",
                "failure_class": "",
                "lock_ref": "paper/build/dependency_environment_lock.json",
                "lock_sha256": "sha256:test-display-env-lock",
                "environment_ref": "test-prepared-display-env",
                "cache_key": "test-display-env-cache",
                "target_platform": "test-platform",
                "binary_checks": [{"name": "Rscript", "status": "present"}],
                "package_checks": [
                    {"name": "ggplot2", "status": "present"},
                    {"name": "ggconsort", "status": "present"},
                ],
                "system_requirement_checks": [],
                "run_context_ref": "paper/build/dependency_run_context.json",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def build_display_surface_workspace(
    tmp_path: Path,
    *,
    include_evidence: bool = False,
    include_extended_evidence: bool = False,
) -> Path:
    paper_root = tmp_path / "paper"
    include_evidence = include_evidence or include_extended_evidence
    displays = _build_workspace_registry_displays(
        include_evidence=include_evidence,
        include_extended_evidence=include_extended_evidence,
    )
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": displays,
        },
    )
    dump_json(
        paper_root / "figures" / "Figure1.shell.json",
        {
            "schema_version": 1,
            "display_id": "Figure1",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "catalog_id": "F1",
        },
    )
    dump_json(
        paper_root / "tables" / "Table1.shell.json",
        {
            "schema_version": 1,
            "display_id": "Table1",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
        },
    )
    if include_evidence:
        for figure_index, template_id in _workspace_template_bindings(include_extended_evidence):
            dump_json(
                paper_root / "figures" / f"Figure{figure_index}.shell.json",
                {
                    "schema_version": 1,
                    "display_id": f"Figure{figure_index}",
                    "display_kind": "figure",
                    "requirement_key": template_id,
                },
            )
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Study cohort flow",
            "steps": [
                {
                    "step_id": "screened",
                    "label": "Patients screened",
                    "n": 186,
                    "detail": "Consecutive surgical cases",
                },
                {
                    "step_id": "eligible",
                    "label": "Eligible after criteria review",
                    "n": 142,
                    "detail": "Complete preoperative variables",
                },
                {
                    "step_id": "included",
                    "label": "Included in analysis",
                    "n": 128,
                    "detail": "Primary cohort",
                },
            ],
        },
    )
    if include_evidence:
        allowed_template_ids = {
            template_id for _, template_id in _workspace_template_bindings(include_extended_evidence)
        }
        for filename, envelope in _current_evidence_input_envelopes().items():
            displays_for_envelope = [
                display
                for display in envelope["displays"]
                if str(display.get("template_id") or "").rsplit("::", 1)[-1] in allowed_template_ids
            ]
            if displays_for_envelope:
                updated = {**envelope, "displays": displays_for_envelope}
                dump_json(paper_root / filename, updated)
    dump_json(
        paper_root / "baseline_characteristics_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": display_registry.get_table_shell_spec("table1_baseline_characteristics").shell_id,
            "display_id": "Table1",
            "title": "Baseline characteristics",
            "groups": [
                {"group_id": "overall", "label": "Overall (n=128)"},
                {"group_id": "low_risk", "label": "Low risk (n=73)"},
                {"group_id": "high_risk", "label": "High risk (n=55)"},
            ],
            "variables": [
                {
                    "variable_id": "age",
                    "label": "Age, median (IQR)",
                    "values": ["52 (44-61)", "49 (42-56)", "58 (50-66)"],
                },
                {
                    "variable_id": "female",
                    "label": "Female sex, n (%)",
                    "values": ["71 (55.5)", "45 (61.6)", "26 (47.3)"],
                },
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    _write_prepared_dependency_environment(paper_root)
    return paper_root
