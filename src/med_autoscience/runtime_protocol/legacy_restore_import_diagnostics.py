from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LegacyRestoreImportDiagnosticPath:
    path: Path
    source_kind: str
    legacy: bool = True
    diagnostic: bool = True


def legacy_restore_import_diagnostic_latest_paper_bundle_manifest(
    quest_root: Path,
) -> LegacyRestoreImportDiagnosticPath | None:
    from med_autoscience.runtime_protocol import paper_artifacts

    path = paper_artifacts.resolve_paper_bundle_manifest(
        quest_root,
        legacy_restore_import_diagnostic=True,
    )
    if path is None:
        return None
    return LegacyRestoreImportDiagnosticPath(
        path=path.resolve(),
        source_kind="paper_bundle_manifest",
    )


__all__ = [
    "LegacyRestoreImportDiagnosticPath",
    "legacy_restore_import_diagnostic_latest_paper_bundle_manifest",
]
