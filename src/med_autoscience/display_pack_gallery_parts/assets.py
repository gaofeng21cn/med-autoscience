from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import shutil

from med_autoscience.display_pack_gallery_parts import paths


@dataclass(frozen=True)
class RenderedAsset:
    status: str
    image_ref: str = ""
    preview_image_ref: str = ""
    payload_ref: str = ""
    layout_ref: str = ""
    pdf_ref: str = ""
    svg_ref: str = ""
    reason: str = ""
    image_size_px: tuple[int, int] = (0, 0)
    preview_image_size_px: tuple[int, int] = (0, 0)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _image_size(path: Path) -> tuple[int, int]:
    try:
        from PIL import Image
    except ImportError:
        return (0, 0)
    with Image.open(path) as image:
        return image.size


def _square_gallery_preview(path: Path) -> tuple[Path, tuple[int, int]]:
    try:
        from PIL import Image
    except ImportError:
        return (path, _image_size(path))
    with Image.open(path) as image:
        width, height = image.size
        if width == height:
            return (path, (width, height))
        side = max(width, height)
        preview_path = path.with_name(f"{path.stem}.gallery.png")
        canvas = Image.new("RGB", (side, side), "white")
        source = image.convert("RGBA")
        paste_position = ((side - width) // 2, (side - height) // 2)
        canvas.paste(source, paste_position, source)
        canvas.save(preview_path, format="PNG")
        return (preview_path, (side, side))


def _relative_ref(path: Path) -> str:
    return str(path.relative_to(paths.HTML_PATH.parent))


def _strip_trailing_whitespace(path: Path) -> None:
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    stripped = "\n".join(line.rstrip() for line in text.splitlines()) + "\n"
    if stripped != text:
        path.write_text(stripped, encoding="utf-8")


def _clean_assets() -> None:
    paths.ASSET_ROOT.mkdir(parents=True, exist_ok=True)
    for path in paths.ASSET_ROOT.iterdir():
        if path.name == "gallery_manifest.json":
            continue
        if path.is_dir():
            shutil.rmtree(path)
        elif path.suffix in {".png", ".pdf", ".json", ".svg"}:
            path.unlink()
    paths.PYTHON_CURRENT_ROOT.mkdir(parents=True, exist_ok=True)
    paths.PYTHON_BASELINE_ROOT.mkdir(parents=True, exist_ok=True)
