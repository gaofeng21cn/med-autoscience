from __future__ import annotations

from pathlib import Path


SUPERVISION_LATEST_RELATIVE_PATH = Path("runtime/artifacts/supervision/opl_current_control_state/latest.json")
SUPERVISION_HISTORY_RELATIVE_PATH = Path("runtime/artifacts/supervision/opl_current_control_state/history.jsonl")
SUPERVISION_REQUEST_ALLOWED_WRITE_SURFACES = ["artifacts/supervision/**"]
SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES = [
    "artifacts/supervision/**",
    "artifacts/autonomy/repair_lifecycle/latest.json",
    "artifacts/autonomy/repair_actions/latest.json",
]
SUPERVISION_FORBIDDEN_ACTIONS = [
    "paper_package_mutation",
    "manual_study_patch",
    "quality_gate_relaxation",
    "medical_claim_authoring",
]
