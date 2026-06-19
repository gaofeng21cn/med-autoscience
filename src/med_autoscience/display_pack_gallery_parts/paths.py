from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[3]
PACK_ROOT = REPO_ROOT / "display-packs" / "fenggaolab.org.medical-display-core"
PACK_SRC_ROOT = PACK_ROOT / "src"
TEMPLATE_ROOT = PACK_ROOT / "templates"
EXAMPLES_ROOT = REPO_ROOT / "docs" / "delivery" / "medical-display" / "examples"
DEFAULT_OUTPUT_ROOT = REPO_ROOT / "outputs" / "display-pack-gallery"
DOCS_PDF_PATH = EXAMPLES_ROOT / "ggplot2_template_gallery.pdf"
DOCS_REFERENCE_PATH = EXAMPLES_ROOT / "ggplot2_template_reference.md"
DOCS_QUALITY_AUDIT_PATH = EXAMPLES_ROOT / "display_pack_gallery_quality_audit.md"
ASSET_ROOT = DEFAULT_OUTPUT_ROOT / "ggplot2_template_reference_assets"
HTML_PATH = DEFAULT_OUTPUT_ROOT / "ggplot2_template_gallery.html"
PDF_PATH = DEFAULT_OUTPUT_ROOT / "ggplot2_template_gallery.pdf"
REFERENCE_PATH = DEFAULT_OUTPUT_ROOT / "ggplot2_template_reference.md"
QUALITY_AUDIT_PATH = DEFAULT_OUTPUT_ROOT / "display_pack_gallery_quality_audit.md"
MANIFEST_PATH = ASSET_ROOT / "gallery_manifest.json"
NATURE_SKILLS_HEAD = "54eadc65d1c0535e90d792a87ab718d848ccbb7a"

if str(PACK_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(PACK_SRC_ROOT))


def configure_output_paths(output_root: Path) -> None:
    global ASSET_ROOT
    global HTML_PATH
    global PDF_PATH
    global REFERENCE_PATH
    global QUALITY_AUDIT_PATH
    global MANIFEST_PATH

    resolved = output_root.expanduser()
    if not resolved.is_absolute():
        resolved = REPO_ROOT / resolved
    resolved = resolved.resolve()
    ASSET_ROOT = resolved / "ggplot2_template_reference_assets"
    HTML_PATH = resolved / "ggplot2_template_gallery.html"
    PDF_PATH = resolved / "ggplot2_template_gallery.pdf"
    REFERENCE_PATH = resolved / "ggplot2_template_reference.md"
    QUALITY_AUDIT_PATH = resolved / "display_pack_gallery_quality_audit.md"
    MANIFEST_PATH = ASSET_ROOT / "gallery_manifest.json"
