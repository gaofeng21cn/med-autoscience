from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


__all__ = [
    "StudyRuntimeArtifacts",
    "StudyRuntimeContext",
]


@dataclass(frozen=True)
class StudyRuntimeContext:
    runtime_root: Path
    quest_root: Path
    runtime_binding_path: Path
    startup_payload_root: Path
    launch_report_path: Path


@dataclass(frozen=True)
class StudyRuntimeArtifacts:
    runtime_binding_path: Path
    launch_report_path: Path
    startup_payload_path: Path | None

    def to_dict(self) -> dict[str, object]:
        return {
            "runtime_binding_path": str(self.runtime_binding_path),
            "launch_report_path": str(self.launch_report_path),
            "startup_payload_path": str(self.startup_payload_path) if self.startup_payload_path is not None else None,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "StudyRuntimeArtifacts":
        if not isinstance(payload, dict):
            raise TypeError("study runtime artifacts payload must be a mapping")
        runtime_binding_path = str(payload.get("runtime_binding_path") or "").strip()
        if not runtime_binding_path:
            raise ValueError("study runtime artifacts payload missing runtime_binding_path")
        launch_report_path = str(payload.get("launch_report_path") or "").strip()
        if not launch_report_path:
            raise ValueError("study runtime artifacts payload missing launch_report_path")
        startup_payload_raw = payload.get("startup_payload_path")
        startup_payload_path: Path | None
        if startup_payload_raw is None or str(startup_payload_raw).strip() == "":
            startup_payload_path = None
        else:
            startup_payload_path = Path(str(startup_payload_raw))
        return cls(
            runtime_binding_path=Path(runtime_binding_path),
            launch_report_path=Path(launch_report_path),
            startup_payload_path=startup_payload_path,
        )
