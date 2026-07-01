from __future__ import annotations

from pathlib import Path
import sys

from med_autoscience.display_pack_paths import core_medical_display_pack_root

REPO_ROOT = Path(__file__).resolve().parents[3]
PACK_ROOT = core_medical_display_pack_root(REPO_ROOT)
PACK_SRC_ROOT = PACK_ROOT / "src"
TEMPLATE_ROOT = PACK_ROOT / "templates"
CATALOGS_ROOT = REPO_ROOT / "docs" / "delivery" / "medical-display" / "catalogs"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "outputs" / "display-pack-gallery"
DOCS_TEMPLATE_CATALOG_PATH = CATALOGS_ROOT / "medical_display_template_catalog.md"
ASSET_ROOT = DEFAULT_OUTPUT_ROOT / "medical_display_gallery_assets"
HTML_PATH = DEFAULT_OUTPUT_ROOT / "medical_display_gallery.html"
PDF_PATH = DEFAULT_OUTPUT_ROOT / "medical_display_gallery.pdf"
REFERENCE_PATH = DEFAULT_OUTPUT_ROOT / "medical_display_gallery_reference.md"
QUALITY_AUDIT_PATH = DEFAULT_OUTPUT_ROOT / "display_pack_gallery_quality_audit.md"
LIDOCAINEQ_PARITY_AUDIT_PATH = DEFAULT_OUTPUT_ROOT / "lidocaineq_visual_parity_audit.md"
LIDOCAINEQ_PARITY_AUDIT_JSON_PATH = DEFAULT_OUTPUT_ROOT / "lidocaineq_visual_parity_audit.json"
LIDOCAINEQ_PARITY_CONTACT_SHEET_PATH = DEFAULT_OUTPUT_ROOT / "lidocaineq_visual_parity_contact_sheet.png"
STATUS_PATH = DEFAULT_OUTPUT_ROOT / "display_pack_gallery_status.md"
MANIFEST_PATH = ASSET_ROOT / "gallery_manifest.json"
NATURE_SKILLS_HEAD = "5d2ba1dee1c087be6de8f4a8aad4b27f04974be9"

if str(PACK_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(PACK_SRC_ROOT))


def configure_output_paths(output_root: Path) -> None:
    global ASSET_ROOT
    global HTML_PATH
    global PDF_PATH
    global REFERENCE_PATH
    global QUALITY_AUDIT_PATH
    global LIDOCAINEQ_PARITY_AUDIT_PATH
    global LIDOCAINEQ_PARITY_AUDIT_JSON_PATH
    global LIDOCAINEQ_PARITY_CONTACT_SHEET_PATH
    global STATUS_PATH
    global MANIFEST_PATH

    resolved = output_root.expanduser()
    if not resolved.is_absolute():
        resolved = REPO_ROOT / resolved
    resolved = resolved.resolve()
    ASSET_ROOT = resolved / "medical_display_gallery_assets"
    HTML_PATH = resolved / "medical_display_gallery.html"
    PDF_PATH = resolved / "medical_display_gallery.pdf"
    REFERENCE_PATH = resolved / "medical_display_gallery_reference.md"
    QUALITY_AUDIT_PATH = resolved / "display_pack_gallery_quality_audit.md"
    LIDOCAINEQ_PARITY_AUDIT_PATH = resolved / "lidocaineq_visual_parity_audit.md"
    LIDOCAINEQ_PARITY_AUDIT_JSON_PATH = resolved / "lidocaineq_visual_parity_audit.json"
    LIDOCAINEQ_PARITY_CONTACT_SHEET_PATH = resolved / "lidocaineq_visual_parity_contact_sheet.png"
    STATUS_PATH = resolved / "display_pack_gallery_status.md"
    MANIFEST_PATH = ASSET_ROOT / "gallery_manifest.json"


def repo_relative_path(value: Path | str) -> str:
    path = Path(value)
    if not path.is_absolute():
        return str(path)
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)
