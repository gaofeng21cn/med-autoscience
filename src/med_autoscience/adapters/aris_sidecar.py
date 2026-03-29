from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Mapping


REQUIRED_HANDOFF_FILES = (
    "algorithm_scout_report.md",
    "innovation_hypotheses.md",
    "final_method_proposal.md",
    "experiment_plan.md",
    "experiment_results_summary.md",
    "review_loop_summary.md",
    "prior_limitations.md",
    "why_our_method_can_work.md",
    "claim_to_evidence_map.md",
    "sidecar_manifest.json",
)


def sidecar_root(quest_root: Path) -> Path:
    return Path(quest_root).expanduser().resolve() / "sidecars" / "aris"


def handoff_root(quest_root: Path) -> Path:
    return sidecar_root(quest_root) / "handoff"


def artifact_root(quest_root: Path) -> Path:
    return Path(quest_root).expanduser().resolve() / "artifacts" / "algorithm_research" / "aris"


def dump_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def build_contract_hash(payload: Mapping[str, Any]) -> str:
    canonical = json.dumps(dict(payload), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def required_handoff_files() -> tuple[str, ...]:
    return REQUIRED_HANDOFF_FILES


def copy_file(*, source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
