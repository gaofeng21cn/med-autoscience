from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.controllers import data_assets
from med_autoscience.policies import data_asset_gate as data_asset_gate_policy
from med_autoscience.runtime_protocol import quest_state, user_message
from med_autoscience.runtime_protocol import report_store as runtime_protocol_report_store


@dataclass
class DataAssetGateState:
    quest_root: Path
    runtime_state: dict[str, Any]
    workspace_root: Path
    study_id: str
    impact_report: dict[str, Any]
    study_report: dict[str, Any] | None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def read_quest_id(quest_root: Path) -> str:
    quest_yaml_path = quest_root / "quest.yaml"
    payload = yaml.safe_load(quest_yaml_path.read_text(encoding="utf-8")) or {}
    if isinstance(payload, dict):
        startup_contract = payload.get("startup_contract")
        if isinstance(startup_contract, dict):
            runtime_reentry_gate = startup_contract.get("runtime_reentry_gate")
            if isinstance(runtime_reentry_gate, dict):
                study_id = runtime_reentry_gate.get("study_id")
                if isinstance(study_id, str) and study_id:
                    return study_id
        quest_id = payload.get("quest_id")
        if isinstance(quest_id, str) and quest_id:
            return quest_id
    return quest_root.name


def resolve_workspace_root(quest_root: Path) -> Path:
    return quest_root.parents[4]


def find_study_report(impact_report: dict[str, Any], study_id: str) -> dict[str, Any] | None:
    for item in impact_report.get("studies", []) or []:
        if isinstance(item, dict) and item.get("study_id") == study_id:
            return item
    return None


def build_gate_state(quest_root: Path) -> DataAssetGateState:
    runtime_state = quest_state.load_runtime_state(quest_root)
    workspace_root = resolve_workspace_root(quest_root)
    study_id = read_quest_id(quest_root)
    impact_report = data_assets.assess_data_asset_impact(workspace_root=workspace_root)
    study_report = find_study_report(impact_report, study_id)
    return DataAssetGateState(
        quest_root=quest_root,
        runtime_state=runtime_state,
        workspace_root=workspace_root,
        study_id=study_id,
        impact_report=impact_report,
        study_report=study_report,
    )


def build_gate_report(state: DataAssetGateState) -> dict[str, Any]:
    dataset_inputs = list((state.study_report or {}).get("dataset_inputs") or [])
    blockers: list[str] = []
    advisories: list[str] = []
    outdated_dataset_ids = [
        str(item.get("dataset_id"))
        for item in dataset_inputs
        if item.get("private_version_status") == "older_than_latest"
    ]
    unresolved_dataset_ids = [
        str(item.get("dataset_id"))
        for item in dataset_inputs
        if item.get("private_version_status") in {"unversioned_path", "family_not_registered"}
        or item.get("private_contract_status") in {"directory_scan_only", "release_not_registered"}
    ]
    public_support_dataset_ids = sorted(
        {
            public_dataset_id
            for item in dataset_inputs
            for public_dataset_id in (item.get("public_support_dataset_ids") or [])
            if isinstance(public_dataset_id, str)
        }
    )

    if outdated_dataset_ids:
        blockers.append("outdated_private_release")
    if unresolved_dataset_ids:
        blockers.append("unresolved_private_data_contract")
    if public_support_dataset_ids:
        advisories.append("public_data_extension_available")
    if state.study_report is None:
        blockers.append("missing_study_data_impact_entry")

    if blockers:
        status = "blocked"
        recommended_action = data_asset_gate_policy.BLOCKED_RECOMMENDED_ACTION
    elif advisories:
        status = "advisory"
        recommended_action = data_asset_gate_policy.ADVISORY_RECOMMENDED_ACTION
    else:
        status = "clear"
        recommended_action = data_asset_gate_policy.CLEAR_RECOMMENDED_ACTION

    return {
        "schema_version": 1,
        "gate_kind": "data_asset_control",
        "generated_at": utc_now(),
        "quest_id": state.quest_root.name,
        "study_id": state.study_id,
        "workspace_root": str(state.workspace_root),
        "impact_report_path": str(data_assets._impact_report_path(state.workspace_root)),
        "status": status,
        "recommended_action": recommended_action,
        "blockers": blockers,
        "advisories": advisories,
        "study_status": (state.study_report or {}).get("status"),
        "outdated_dataset_ids": outdated_dataset_ids,
        "unresolved_dataset_ids": unresolved_dataset_ids,
        "public_support_dataset_ids": public_support_dataset_ids,
        "dataset_inputs": dataset_inputs,
        "controller_note": data_asset_gate_policy.CONTROLLER_NOTE,
    }


def render_gate_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Data Asset Gate Report",
        "",
        f"- generated_at: `{report['generated_at']}`",
        f"- study_id: `{report['study_id']}`",
        f"- status: `{report['status']}`",
        f"- recommended_action: `{report['recommended_action']}`",
        "",
        "## Blockers",
        "",
    ]
    blockers = report.get("blockers") or []
    if blockers:
        lines.extend(f"- `{item}`" for item in blockers)
    else:
        lines.append("- None")
    lines.extend(["", "## Advisories", ""])
    advisories = report.get("advisories") or []
    if advisories:
        lines.extend(f"- `{item}`" for item in advisories)
    else:
        lines.append("- None")
    lines.extend(
        [
            "",
            "## Study Data State",
            "",
            f"- `study_status`: `{report.get('study_status')}`",
            f"- `outdated_dataset_ids`: `{', '.join(report.get('outdated_dataset_ids') or ['none'])}`",
            f"- `public_support_dataset_ids`: `{', '.join(report.get('public_support_dataset_ids') or ['none'])}`",
            "",
            "## Controller Scope",
            "",
            f"- {report.get('controller_note')}",
            "",
        ]
    )
    return "\n".join(lines)


def write_gate_files(quest_root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    return runtime_protocol_report_store.write_timestamped_report(
        quest_root=quest_root,
        report_group="data_asset_gate",
        timestamp=str(report["generated_at"]),
        report=report,
        markdown=render_gate_markdown(report),
    )


def run_controller(
    *,
    quest_root: Path,
    apply: bool,
    source: str = "codex-data-asset-gate",
) -> dict[str, Any]:
    state = build_gate_state(quest_root)
    report = build_gate_report(state)
    json_path, md_path = write_gate_files(quest_root, report)
    intervention = None
    if apply and report["status"] in {"blocked", "advisory"}:
        intervention = user_message.enqueue_user_message(
            quest_root=state.quest_root,
            runtime_state=state.runtime_state,
            message=data_asset_gate_policy.build_intervention_message(report),
            source=source,
        )
    return {
        "report_json": str(json_path),
        "report_markdown": str(md_path),
        "status": report["status"],
        "blockers": report["blockers"],
        "advisories": report["advisories"],
        "study_id": report["study_id"],
        "outdated_dataset_ids": report["outdated_dataset_ids"],
        "unresolved_dataset_ids": report["unresolved_dataset_ids"],
        "public_support_dataset_ids": report["public_support_dataset_ids"],
        "intervention_enqueued": bool(intervention),
        "message_id": intervention.get("message_id") if intervention else None,
        "source": source,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quest-root", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    print(json.dumps(run_controller(quest_root=args.quest_root, apply=args.apply), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
