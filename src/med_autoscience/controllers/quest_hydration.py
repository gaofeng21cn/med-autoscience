from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from med_autoscience import startup_literature
from med_autoscience.controllers._medical_display_surface_support import (
    build_required_display_surface_stub_payload,
    resolve_required_display_surface_stub,
)
from med_autoscience.controllers import literature_hydration as literature_hydration_controller
from med_autoscience import publication_display_contract
from med_autoscience.controllers import paper_artifacts
from med_autoscience.workspace_contracts import workspace_literature_status


class StartupHydrationStatus(StrEnum):
    HYDRATED = "hydrated"


@dataclass(frozen=True)
class StartupHydrationReport:
    status: StartupHydrationStatus
    recorded_at: str
    quest_root: str
    entry_state_summary: str
    literature_report: dict[str, Any]
    written_files: tuple[str, ...]
    report_path: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", self._normalize_status(self.status))
        object.__setattr__(self, "written_files", tuple(str(item) for item in self.written_files))
        if self.report_path is not None:
            object.__setattr__(self, "report_path", str(self.report_path))

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "status": self.status.value,
            "recorded_at": self.recorded_at,
            "quest_root": self.quest_root,
            "entry_state_summary": self.entry_state_summary,
            "literature_report": dict(self.literature_report),
            "written_files": list(self.written_files),
        }
        if self.report_path is not None:
            payload["report_path"] = self.report_path
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StartupHydrationReport":
        if not isinstance(payload, dict):
            raise TypeError("startup hydration payload must be a mapping")
        if "recorded_at" not in payload or not str(payload.get("recorded_at") or "").strip():
            raise ValueError("startup hydration payload missing recorded_at")
        if "quest_root" not in payload or not str(payload.get("quest_root") or "").strip():
            raise ValueError("startup hydration payload missing quest_root")
        if "entry_state_summary" not in payload or not str(payload.get("entry_state_summary") or "").strip():
            raise ValueError("startup hydration payload missing entry_state_summary")
        written_files = payload.get("written_files") or []
        if not isinstance(written_files, list):
            raise ValueError("startup hydration payload written_files must be a list")
        if "literature_report" not in payload:
            raise ValueError("startup hydration payload missing literature_report")
        literature_report = payload.get("literature_report") or {}
        if not isinstance(literature_report, dict):
            raise ValueError("startup hydration payload literature_report must be a mapping")
        return cls(
            status=payload.get("status"),
            recorded_at=str(payload.get("recorded_at") or ""),
            quest_root=str(payload.get("quest_root") or ""),
            entry_state_summary=str(payload.get("entry_state_summary") or ""),
            literature_report=dict(literature_report),
            written_files=tuple(str(item) for item in written_files),
            report_path=str(payload.get("report_path") or "") or None,
        )

    @staticmethod
    def _normalize_status(value: StartupHydrationStatus | str) -> StartupHydrationStatus:
        if isinstance(value, StartupHydrationStatus):
            return value
        if not isinstance(value, str):
            raise TypeError("status must be str")
        try:
            return StartupHydrationStatus(value)
        except ValueError as exc:
            raise ValueError(f"unknown startup hydration status: {value}") from exc


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        Path(temp_name).replace(path)
    finally:
        if temp_name is not None:
            Path(temp_name).unlink(missing_ok=True)


def build_hydration_payload(
    *,
    create_payload: dict[str, Any],
    study_root: Path | None = None,
    workspace_root: Path | None = None,
) -> dict[str, object]:
    startup_contract = create_payload.get("startup_contract")
    if not isinstance(startup_contract, dict):
        raise ValueError("create payload missing startup_contract")
    medical_analysis_contract = startup_contract.get("medical_analysis_contract_summary")
    if not isinstance(medical_analysis_contract, dict):
        raise ValueError("startup_contract missing medical_analysis_contract_summary")
    medical_reporting_contract = startup_contract.get("medical_reporting_contract_summary")
    if not isinstance(medical_reporting_contract, dict):
        raise ValueError("startup_contract missing medical_reporting_contract_summary")
    entry_state_summary = startup_contract.get("entry_state_summary")
    if not isinstance(entry_state_summary, str) or not entry_state_summary.strip():
        raise ValueError("startup_contract missing entry_state_summary")
    payload: dict[str, object] = {
        "medical_analysis_contract": dict(medical_analysis_contract),
        "medical_reporting_contract": dict(medical_reporting_contract),
        "entry_state_summary": entry_state_summary.strip(),
        "literature_records": startup_literature.resolve_startup_literature_records(startup_contract=startup_contract),
    }
    if (study_root is None) != (workspace_root is None):
        raise ValueError("study_root and workspace_root must be provided together")
    if study_root is None or workspace_root is None:
        return payload

    from med_autoscience import study_reference_context

    reference_context = study_reference_context.build_study_reference_context(
        study_root=study_root,
        workspace_root=workspace_root,
        startup_contract=startup_contract,
    )
    payload["workspace_literature"] = workspace_literature_status(workspace_root=workspace_root)
    payload["study_reference_context"] = reference_context
    payload["literature_records"] = list(reference_context.get("records") or [])
    return payload


def write_startup_hydration_report(
    *,
    quest_root: Path,
    report: StartupHydrationReport,
) -> StartupHydrationReport:
    path = Path(quest_root).expanduser().resolve() / "artifacts" / "reports" / "startup" / "hydration_report.json"
    payload = report.to_dict()
    payload["report_path"] = str(path)
    _write_json(path, payload)
    return StartupHydrationReport.from_payload(payload)


def _read_json_dict(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object at {path}")
    return payload


def _require_dict(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"hydration payload must contain mapping: {key}")
    return dict(value)


def _require_str(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"hydration payload must contain non-empty string: {key}")
    return value.strip()


def _optional_record_list(payload: dict[str, object], key: str) -> list[dict[str, object]]:
    value = payload.get(key)
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"hydration payload must contain list when provided: {key}")
    records: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError(f"hydration payload {key} must contain mappings")
        records.append(dict(item))
    return records


def _optional_mapping(payload: dict[str, object], key: str) -> dict[str, object] | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError(f"hydration payload must contain mapping when provided: {key}")
    return dict(value)


def _is_legacy_display_id(*, display_id: str, display_kind: str) -> bool:
    item = str(display_id).strip()
    kind = str(display_kind).strip()
    if kind == "figure":
        return bool(item) and item.lower().startswith("figure") and item[6:].isdigit()
    if kind == "table":
        return bool(item) and item.lower().startswith("table") and item[5:].isdigit()
    return False


def _normalize_display_shell_plan(reporting_contract: dict[str, object]) -> list[dict[str, str]]:
    plan = reporting_contract.get("display_shell_plan")
    normalized: list[dict[str, str]] = []
    if isinstance(plan, list):
        for item in plan:
            if not isinstance(item, dict):
                raise ValueError("medical_reporting_contract.display_shell_plan must contain mappings")
            display_id_value = item.get("display_id")
            display_kind_value = item.get("display_kind")
            requirement_key_value = item.get("requirement_key")
            if not isinstance(display_id_value, str) or not display_id_value.strip():
                raise ValueError(
                    "medical_reporting_contract.display_shell_plan items must include non-empty string display_id"
                )
            if not isinstance(display_kind_value, str) or not display_kind_value.strip():
                raise ValueError(
                    "medical_reporting_contract.display_shell_plan items must include non-empty string display_kind"
                )
            if not isinstance(requirement_key_value, str) or not requirement_key_value.strip():
                raise ValueError(
                    "medical_reporting_contract.display_shell_plan items must include non-empty string requirement_key"
                )
            display_id = display_id_value.strip()
            display_kind = display_kind_value.strip()
            requirement_key = requirement_key_value.strip()
            catalog_id = ""
            if "catalog_id" in item:
                catalog_id_value = item.get("catalog_id")
                if catalog_id_value is None:
                    catalog_id = ""
                elif not isinstance(catalog_id_value, str):
                    raise ValueError(
                        "medical_reporting_contract.display_shell_plan items must include string catalog_id when provided"
                    )
                else:
                    catalog_id = catalog_id_value.strip()
            if not display_id or not display_kind or not requirement_key:
                raise ValueError(
                    "medical_reporting_contract.display_shell_plan items must include display_id, display_kind, requirement_key"
                )
            if resolve_required_display_surface_stub(requirement_key) is None:
                raise ValueError(
                    f"medical_reporting_contract.display_shell_plan contains unsupported requirement_key: {requirement_key}"
                )
            if not catalog_id and not _is_legacy_display_id(display_id=display_id, display_kind=display_kind):
                raise ValueError(
                    "medical_reporting_contract.display_shell_plan semantic display_id items must include catalog_id"
                )
            normalized_item = {
                "display_id": display_id,
                "display_kind": display_kind,
                "requirement_key": requirement_key,
            }
            if catalog_id:
                normalized_item["catalog_id"] = catalog_id
            normalized.append(normalized_item)
        return normalized

    legacy_plan: list[dict[str, str]] = []
    figure_shell_requirements = list(reporting_contract.get("figure_shell_requirements") or [])
    table_shell_requirements = list(reporting_contract.get("table_shell_requirements") or [])
    cohort_flow_required = reporting_contract.get("cohort_flow_required")
    baseline_required = reporting_contract.get("baseline_characteristics_required")
    if cohort_flow_required is False:
        cohort_flow_enabled = False
    elif figure_shell_requirements:
        cohort_flow_enabled = "cohort_flow_figure" in figure_shell_requirements
    else:
        cohort_flow_enabled = True
    if baseline_required is False:
        baseline_enabled = False
    elif table_shell_requirements:
        baseline_enabled = "table1_baseline_characteristics" in table_shell_requirements
    else:
        baseline_enabled = True

    if cohort_flow_enabled:
        legacy_plan.append(
            {
                "display_id": "cohort_flow",
                "display_kind": "figure",
                "requirement_key": "cohort_flow_figure",
                "catalog_id": "F1",
            }
        )
    if baseline_enabled:
        legacy_plan.append(
            {
                "display_id": "baseline_characteristics",
                "display_kind": "table",
                "requirement_key": "table1_baseline_characteristics",
                "catalog_id": "T1",
            }
        )
    return legacy_plan


def _write_json_if_missing(path: Path, payload: dict[str, Any]) -> bool:
    if path.exists():
        return False
    _write_json(path, payload)
    return True


def _write_json_if_changed(path: Path, payload: dict[str, Any]) -> bool:
    if path.exists():
        current_payload = _read_json_dict(path)
        if current_payload == payload:
            return False
    _write_json(path, payload)
    return True


def _has_substantive_surface_content(payload: dict[str, Any], *, requirement_key: str) -> bool:
    spec = resolve_required_display_surface_stub(requirement_key)
    if spec is None:
        return False
    if spec.stub_kind == "cohort_flow":
        return isinstance(payload.get("steps"), list) and bool(payload.get("steps"))
    if spec.stub_kind == "table_shell":
        return (
            (isinstance(payload.get("groups"), list) and bool(payload.get("groups")))
            or (isinstance(payload.get("variables"), list) and bool(payload.get("variables")))
            or (isinstance(payload.get("columns"), list) and bool(payload.get("columns")))
            or (isinstance(payload.get("rows"), list) and bool(payload.get("rows")))
        )
    displays = payload.get("displays")
    if not isinstance(displays, list) or not displays:
        return False
    for item in displays:
        if not isinstance(item, dict):
            continue
        substantive_keys = {
            key
            for key, value in item.items()
            if value not in (None, "", [], {})
            and key not in {"display_id", "template_id", "catalog_id"}
        }
        if substantive_keys:
            return True
    return False


def _merge_evidence_input_displays(
    *,
    existing_displays: object,
    stub_displays: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not isinstance(existing_displays, list) or not existing_displays:
        return [dict(item) for item in stub_displays]

    normalized_existing = [dict(item) for item in existing_displays if isinstance(item, dict)]
    if not normalized_existing:
        return [dict(item) for item in stub_displays]

    if len(stub_displays) != 1:
        return [dict(item) for item in stub_displays]

    stub_item = dict(stub_displays[0])
    if len(normalized_existing) == 1:
        merged_item = dict(normalized_existing[0])
        merged_item.update(stub_item)
        return [merged_item]

    matched = False
    merged_displays: list[dict[str, Any]] = []
    stub_catalog_id = str(stub_item.get("catalog_id") or "").strip()
    stub_template_id = str(stub_item.get("template_id") or "").strip()
    stub_display_id = str(stub_item.get("display_id") or "").strip()
    for item in normalized_existing:
        item_catalog_id = str(item.get("catalog_id") or "").strip()
        item_template_id = str(item.get("template_id") or "").strip()
        item_display_id = str(item.get("display_id") or "").strip()
        if not matched and (
            (stub_catalog_id and item_catalog_id == stub_catalog_id)
            or (stub_template_id and item_template_id == stub_template_id)
            or (stub_display_id and item_display_id == stub_display_id)
        ):
            merged_item = dict(item)
            merged_item.update(stub_item)
            merged_displays.append(merged_item)
            matched = True
        else:
            merged_displays.append(item)
    if not matched:
        merged_displays.insert(0, stub_item)
    return merged_displays


def _merge_surface_stub_payload(
    *,
    path: Path,
    requirement_key: str,
    stub_payload: dict[str, Any],
) -> dict[str, Any]:
    if not path.exists():
        return dict(stub_payload)

    existing_payload = _read_json_dict(path)
    if not _has_substantive_surface_content(existing_payload, requirement_key=requirement_key):
        return dict(stub_payload)

    merged_payload = dict(existing_payload)
    for key in ("schema_version", "source_contract_path", "display_id", "catalog_id"):
        if key in stub_payload:
            merged_payload[key] = stub_payload[key]

    spec = resolve_required_display_surface_stub(requirement_key)
    if spec is not None:
        merged_payload[spec.schema_key] = stub_payload[spec.schema_key]

    if spec is not None and spec.stub_kind == "display_inputs":
        merged_payload["displays"] = _merge_evidence_input_displays(
            existing_displays=existing_payload.get("displays"),
            stub_displays=list(stub_payload.get("displays") or []),
        )
    return merged_payload


def _write_display_surface_stubs(
    *,
    paper_root: Path,
    reporting_contract: dict[str, object],
) -> list[str]:
    reporting_contract_relpath = "paper/medical_reporting_contract.json"
    display_shell_plan = _normalize_display_shell_plan(reporting_contract)
    written_files: list[str] = []

    display_registry_required = bool(reporting_contract.get("display_registry_required", bool(display_shell_plan)))
    display_registry_path = paper_root / "display_registry.json"
    display_registry_payload = {
        "schema_version": 1,
        "source_contract_path": reporting_contract_relpath,
        "displays": [
            {
                **item,
                "shell_path": (
                    f"paper/figures/{item['display_id']}.shell.json"
                    if item["display_kind"] == "figure"
                    else f"paper/tables/{item['display_id']}.shell.json"
                ),
            }
            for item in display_shell_plan
        ],
    }
    if display_registry_required and _write_json_if_changed(display_registry_path, display_registry_payload):
        written_files.append(str(display_registry_path))

    for item in display_shell_plan:
        if item["display_kind"] == "figure":
            shell_path = paper_root / "figures" / f"{item['display_id']}.shell.json"
        else:
            shell_path = paper_root / "tables" / f"{item['display_id']}.shell.json"
        shell_payload = {
            "schema_version": 1,
            "source_contract_path": reporting_contract_relpath,
            "display_id": item["display_id"],
            "display_kind": item["display_kind"],
            "requirement_key": item["requirement_key"],
        }
        if item.get("catalog_id"):
            shell_payload["catalog_id"] = item["catalog_id"]
        if _write_json_if_changed(shell_path, shell_payload):
            written_files.append(str(shell_path))

        stub = build_required_display_surface_stub_payload(
            item=item,
            reporting_contract_relpath=reporting_contract_relpath,
        )
        if stub is None:
            continue
        stub_filename, stub_payload = stub
        stub_path = paper_root / stub_filename
        synced_stub_payload = _merge_surface_stub_payload(
            path=stub_path,
            requirement_key=item["requirement_key"],
            stub_payload=stub_payload,
        )
        if _write_json_if_changed(stub_path, synced_stub_payload):
            written_files.append(str(stub_path))

    return written_files


def _seed_publication_display_contracts(*, paper_root: Path) -> list[str]:
    # Keep hydration seeding aligned with the authoritative publication-display defaults.
    return publication_display_contract.seed_publication_display_contracts_if_missing(paper_root=paper_root)


def materialize_display_contract_stubs(*, paper_root: Path, reporting_contract: dict[str, object] | None = None) -> dict[str, object]:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    resolved_reporting_contract = (
        dict(reporting_contract)
        if isinstance(reporting_contract, dict)
        else _read_json_dict(resolved_paper_root / "medical_reporting_contract.json")
    )
    written_files = [
        *_write_display_surface_stubs(
            paper_root=resolved_paper_root,
            reporting_contract=resolved_reporting_contract,
        ),
        *_seed_publication_display_contracts(paper_root=resolved_paper_root),
    ]
    return {
        "status": "materialized",
        "paper_root": str(resolved_paper_root),
        "reporting_contract_path": str(resolved_paper_root / "medical_reporting_contract.json"),
        "display_registry_path": str(resolved_paper_root / "display_registry.json"),
        "written_files": written_files,
    }


def _resolve_hydration_paper_roots(*, quest_root: Path) -> tuple[Path, ...]:
    roots: list[Path] = [(quest_root / "paper").resolve()]
    try:
        active_paper_root = paper_artifacts.resolve_latest_paper_root(quest_root)
    except FileNotFoundError:
        active_paper_root = None
    if active_paper_root is not None:
        resolved_active_paper_root = active_paper_root.resolve()
        if resolved_active_paper_root not in roots:
            roots.append(resolved_active_paper_root)
    return tuple(roots)


def run_hydration(*, quest_root: Path, hydration_payload: dict[str, object]) -> dict[str, object]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    medical_analysis_contract = _require_dict(hydration_payload, "medical_analysis_contract")
    medical_reporting_contract = _require_dict(hydration_payload, "medical_reporting_contract")
    entry_state_summary = _require_str(hydration_payload, "entry_state_summary")
    literature_records = _optional_record_list(hydration_payload, "literature_records")
    workspace_literature = _optional_mapping(hydration_payload, "workspace_literature")
    study_reference_context = _optional_mapping(hydration_payload, "study_reference_context")
    paper_roots = _resolve_hydration_paper_roots(quest_root=resolved_quest_root)
    written_files: list[str] = []
    for paper_root in paper_roots:
        analysis_path = paper_root / "medical_analysis_contract.json"
        reporting_path = paper_root / "medical_reporting_contract.json"
        _write_json(analysis_path, medical_analysis_contract)
        _write_json(reporting_path, medical_reporting_contract)
        written_files.extend(
            [
                str(analysis_path),
                str(reporting_path),
                *_write_display_surface_stubs(
                    paper_root=paper_root,
                    reporting_contract=medical_reporting_contract,
                ),
                *_seed_publication_display_contracts(paper_root=paper_root),
            ]
        )
    literature_report = literature_hydration_controller.run_literature_hydration(
        quest_root=resolved_quest_root,
        records=literature_records,
        workspace_literature=workspace_literature,
        study_reference_context=study_reference_context,
    )
    written_files.extend(
        [
            literature_report["records_path"],
            literature_report["references_bib_path"],
            literature_report["coverage_report_path"],
        ]
    )
    imported_records_path = literature_report.get("imported_records_path")
    if isinstance(imported_records_path, str) and imported_records_path:
        written_files.append(imported_records_path)
    report = write_startup_hydration_report(
        quest_root=resolved_quest_root,
        report=StartupHydrationReport(
            status=StartupHydrationStatus.HYDRATED,
            recorded_at=_utc_now(),
            quest_root=str(resolved_quest_root),
            entry_state_summary=entry_state_summary,
            literature_report=literature_report,
            written_files=tuple(written_files),
            report_path=None,
        ),
    )
    return report.to_dict()
