from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from med_autoscience.controllers import workspace_literature as workspace_literature_controller


PORTFOLIO_MEMORY_SCHEMA_VERSION = 1
PORTFOLIO_MEMORY_LAYER = "portfolio_research_memory"
ASSET_STATUSES = {"stub", "seeded", "mature"}


@dataclass(frozen=True)
class PortfolioMemoryFile:
    path: Path
    content: str


def _portfolio_memory_root(workspace_root: Path) -> Path:
    return workspace_root / "portfolio" / "research_memory"


def _registry_path(workspace_root: Path) -> Path:
    return _portfolio_memory_root(workspace_root) / "registry.yaml"


def _default_assets() -> list[dict[str, str]]:
    return [
        {
            "asset_id": "topic_landscape",
            "title": "Disease Topic Landscape",
            "path": "topic_landscape.md",
            "status": "stub",
            "purpose": "current high-signal directions for this disease area",
        },
        {
            "asset_id": "dataset_question_map",
            "title": "Dataset Question Map",
            "path": "dataset_question_map.md",
            "status": "stub",
            "purpose": "publishable study directions supported by the workspace datasets",
        },
        {
            "asset_id": "venue_intelligence",
            "title": "Venue Intelligence",
            "path": "venue_intelligence.md",
            "status": "stub",
            "purpose": "journal neighborhood and evidence-backed venue memory across studies",
        },
    ]


def _default_registry_payload() -> dict[str, object]:
    return {
        "schema_version": PORTFOLIO_MEMORY_SCHEMA_VERSION,
        "memory_layer": PORTFOLIO_MEMORY_LAYER,
        "workspace_scope": "disease_workspace",
        "assets": _default_assets(),
    }


def _render_registry_yaml() -> str:
    payload = _default_registry_payload()
    rendered = yaml.safe_dump(payload, allow_unicode=True, sort_keys=False)
    return rendered if rendered.endswith("\n") else f"{rendered}\n"


def _render_readme() -> str:
    return (
        "# Portfolio Research Memory\n\n"
        "这里存放同一 disease workspace 跨多个 future study 可复用的研究资产。\n\n"
        "它不是：\n\n"
        "- 单篇论文的结果目录\n"
        "- MedDeepScientist quest-local memory 的替代品\n"
        "- 临时聊天总结的堆放区\n\n"
        "它主要回答三类问题：\n\n"
        "1. 这个疾病当前哪些研究方向值得持续关注？\n"
        "2. 依托这批核心数据，还能形成哪些独立 study？\n"
        "3. 这类问题通常会落到哪些期刊邻域？\n\n"
        "默认资产：\n\n"
        "- `topic_landscape.md`\n"
        "- `dataset_question_map.md`\n"
        "- `venue_intelligence.md`\n"
        "- `literature/`\n"
        "- `registry.yaml`\n\n"
        "可选增强目录：\n\n"
        "- `prompts/`\n"
        "- `external_reports/`\n\n"
        "更新原则：\n\n"
        "- 只有跨 study 仍然可复用的内容，才写回这里\n"
        "- 单篇论文专属的 framing、shortlist、baseline 结果，仍留在对应 `study/`\n"
        "- 外部调研如果形成稳定结论，应优先回写到这里，而不是只留在 transient chat\n"
        "- `prompts/` 和 `external_reports/` 只是 optional enrichment surface，不是 startup gate\n"
    )


def _render_topic_landscape_stub() -> str:
    return (
        "# Disease Topic Landscape\n\n"
        "## 用途\n\n"
        "记录当前 disease area 内与本 workspace 相关的高信号研究方向。\n\n"
        "## 推荐结构\n\n"
        "1. 当前高信号方向\n"
        "2. 每个方向为什么重要\n"
        "3. 与本 workspace 数据的相关性\n"
        "4. 暂不优先的方向\n"
        "5. 关键来源\n"
    )


def _render_dataset_question_map_stub() -> str:
    return (
        "# Dataset Question Map\n\n"
        "## 用途\n\n"
        "记录基于当前 workspace 核心数据能够形成的独立投稿方向。\n\n"
        "## 推荐结构\n\n"
        "1. 已锁定 study\n"
        "2. 候选 future studies\n"
        "3. 每条方向依赖的数据与终点\n"
        "4. 为什么它应该独立成文，而不是混进现有 study\n"
    )


def _render_venue_intelligence_stub() -> str:
    return (
        "# Venue Intelligence\n\n"
        "## 用途\n\n"
        "记录同一 workspace 内跨多个 study 可复用的期刊邻域判断。\n\n"
        "## 推荐结构\n\n"
        "1. 现实主投带\n"
        "2. stretch 带\n"
        "3. backup 带\n"
        "4. 代表性 similar papers\n"
        "5. 什么时候这些判断可以复用，什么时候必须回到单篇 study 重新判断\n"
    )


def render_portfolio_memory_files(*, workspace_root: Path) -> list[PortfolioMemoryFile]:
    root = _portfolio_memory_root(workspace_root)
    return [
        PortfolioMemoryFile(path=root / "README.md", content=_render_readme()),
        PortfolioMemoryFile(path=root / "registry.yaml", content=_render_registry_yaml()),
        PortfolioMemoryFile(path=root / "topic_landscape.md", content=_render_topic_landscape_stub()),
        PortfolioMemoryFile(path=root / "dataset_question_map.md", content=_render_dataset_question_map_stub()),
        PortfolioMemoryFile(path=root / "venue_intelligence.md", content=_render_venue_intelligence_stub()),
    ]


def _load_registry_payload(workspace_root: Path) -> dict[str, object]:
    path = _registry_path(workspace_root)
    if not path.exists():
        return _default_registry_payload()
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else _default_registry_payload()


def _normalize_assets(raw_assets: object) -> list[dict[str, str]]:
    if not isinstance(raw_assets, list):
        return _default_assets()
    normalized: list[dict[str, str]] = []
    for item in raw_assets:
        if not isinstance(item, dict):
            continue
        asset_id = str(item.get("asset_id") or "").strip()
        title = str(item.get("title") or "").strip()
        path = str(item.get("path") or "").strip()
        purpose = str(item.get("purpose") or "").strip()
        status = str(item.get("status") or "stub").strip()
        if not asset_id or not title or not path or not purpose:
            continue
        if status not in ASSET_STATUSES:
            status = "stub"
        normalized.append(
            {
                "asset_id": asset_id,
                "title": title,
                "path": path,
                "status": status,
                "purpose": purpose,
            }
        )
    return normalized or _default_assets()


def init_portfolio_memory(*, workspace_root: Path) -> dict[str, object]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    root = _portfolio_memory_root(resolved_workspace_root)
    root.mkdir(parents=True, exist_ok=True)
    created_files: list[str] = []
    skipped_files: list[str] = []
    for rendered in render_portfolio_memory_files(workspace_root=resolved_workspace_root):
        if rendered.path.exists():
            skipped_files.append(str(rendered.path))
            continue
        rendered.path.parent.mkdir(parents=True, exist_ok=True)
        rendered.path.write_text(rendered.content, encoding="utf-8")
        created_files.append(str(rendered.path))
    workspace_literature_controller.init_workspace_literature(workspace_root=resolved_workspace_root)
    return {
        "schema_version": PORTFOLIO_MEMORY_SCHEMA_VERSION,
        "workspace_root": str(resolved_workspace_root),
        "portfolio_memory_root": str(root),
        "created_files": created_files,
        "skipped_files": skipped_files,
        "asset_ids": [item["asset_id"] for item in _default_assets()],
    }


def portfolio_memory_status(*, workspace_root: Path) -> dict[str, object]:
    resolved_workspace_root = Path(workspace_root).expanduser().resolve()
    root = _portfolio_memory_root(resolved_workspace_root)
    registry_payload = _load_registry_payload(resolved_workspace_root)
    assets = _normalize_assets(registry_payload.get("assets"))
    asset_rows: list[dict[str, object]] = []
    seeded_asset_count = 0
    existing_asset_count = 0
    for asset in assets:
        asset_path = root / asset["path"]
        exists = asset_path.exists()
        if exists:
            existing_asset_count += 1
        if asset["status"] in {"seeded", "mature"}:
            seeded_asset_count += 1
        asset_rows.append(
            {
                **asset,
                "exists": exists,
                "absolute_path": str(asset_path),
            }
        )
    return {
        "schema_version": PORTFOLIO_MEMORY_SCHEMA_VERSION,
        "workspace_root": str(resolved_workspace_root),
        "portfolio_memory_root": str(root),
        "portfolio_memory_exists": root.exists(),
        "registry_path": str(_registry_path(resolved_workspace_root)),
        "registry_exists": _registry_path(resolved_workspace_root).exists(),
        "memory_layer": str(registry_payload.get("memory_layer") or PORTFOLIO_MEMORY_LAYER),
        "workspace_scope": str(registry_payload.get("workspace_scope") or "disease_workspace"),
        "asset_count": len(asset_rows),
        "existing_asset_count": existing_asset_count,
        "seeded_asset_count": seeded_asset_count,
        "assets": asset_rows,
    }
