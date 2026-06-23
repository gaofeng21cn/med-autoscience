from __future__ import annotations

from pathlib import Path
import tomllib

from med_autoscience.display_pack_loader import load_enabled_local_display_pack_records

CORE_MEDICAL_DISPLAY_PACK_ID = "fenggaolab.org.medical-display-core"
CORE_MEDICAL_DISPLAY_PACK_CONFIG_PATH = "external/display-packs/medical-display-core"
PAPER_CORE_MEDICAL_DISPLAY_PACK_CONFIG_PATH = "paper-external/display-packs/medical-display-core"


def _core_pack_root_if_manifest_matches(candidate: Path) -> Path | None:
    manifest_path = candidate / "display_pack.toml"
    if not manifest_path.is_file():
        return None
    payload = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    if payload.get("pack_id") != CORE_MEDICAL_DISPLAY_PACK_ID:
        return None
    return candidate


def core_medical_display_pack_root(repo_root: Path | str) -> Path:
    candidate = Path(repo_root).expanduser().resolve()
    direct_pack_root = _core_pack_root_if_manifest_matches(candidate)
    if direct_pack_root is not None:
        return direct_pack_root
    for relative_pack_root in (
        CORE_MEDICAL_DISPLAY_PACK_CONFIG_PATH,
        PAPER_CORE_MEDICAL_DISPLAY_PACK_CONFIG_PATH,
        "medical-display-core",
    ):
        direct_pack_root = _core_pack_root_if_manifest_matches(candidate / relative_pack_root)
        if direct_pack_root is not None:
            return direct_pack_root
    records = load_enabled_local_display_pack_records(candidate)
    for record in records:
        if record.pack_manifest.pack_id == CORE_MEDICAL_DISPLAY_PACK_ID:
            return record.pack_root
    raise ValueError(f"enabled display pack `{CORE_MEDICAL_DISPLAY_PACK_ID}` is not configured")


def core_medical_display_template_root(repo_root: Path | str) -> Path:
    return core_medical_display_pack_root(repo_root) / "templates"


def core_medical_display_pack_python_src_root(repo_root: Path | str) -> Path:
    return core_medical_display_pack_root(repo_root) / "src"
